from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import Mapping
from typing import Union

from packaging.utils import canonicalize_name

from poetry.core.json import validate_object
from poetry.core.packages.project_package import ProjectPackage
from poetry.core.pyproject.formats.content_format import ContentFormat
from poetry.core.pyproject.formats.validation_result import ValidationResult
from poetry.core.utils.helpers import combine_unicode
from poetry.core.utils.helpers import readme_content_type


if TYPE_CHECKING:
    from pathlib import Path

    from poetry.core.packages.dependency import Dependency
    from poetry.core.packages.dependency_group import DependencyGroup
    from poetry.core.spdx.license import License

    DependencyConstraint = Union[str, Dict[str, Any]]
    DependencyConfig = Mapping[
        str, Union[List[DependencyConstraint], DependencyConstraint]
    ]


class LegacyContentFormat(ContentFormat):
    @classmethod
    def supports(cls, content: dict[str, Any]) -> bool:
        return (
            "project" not in content
            and "tool" in content
            and "poetry" in content["tool"]
        )

    def validate(self, strict: bool = False) -> ValidationResult:
        result = ValidationResult([], [])

        # We are only interested in the [tool.poetry] table
        config = self._content.get("tool", {}).get("poetry", {})

        # Schema validation errors
        validation_errors = validate_object(config, "poetry-schema")

        result.errors += validation_errors

        if strict:
            # If strict, check the file more thoroughly
            if "dependencies" in config:
                python_versions = config["dependencies"]["python"]
                if python_versions == "*":
                    result.warnings.append(
                        "A wildcard Python dependency is ambiguous. "
                        "Consider specifying a more explicit one."
                    )

                for name, constraint in config["dependencies"].items():
                    if not isinstance(constraint, dict):
                        continue

                    if "allows-prereleases" in constraint:
                        result.warnings.append(
                            f'The "{name}" dependency specifies '
                            'the "allows-prereleases" property, which is deprecated. '
                            'Use "allow-prereleases" instead.'
                        )

            # Checking for scripts with extras
            if "scripts" in config:
                scripts = config["scripts"]
                for name, script in scripts.items():
                    if not isinstance(script, dict):
                        continue

                    extras = script["extras"]
                    for extra in extras:
                        if extra not in config["extras"]:
                            result.errors.append(
                                f'Script "{name}" requires extra "{extra}" which is not'
                                " defined."
                            )

            # Checking types of all readme files (must match)
            if "readme" in config and not isinstance(config["readme"], str):
                readme_types = {readme_content_type(r) for r in config["readme"]}
                if len(readme_types) > 1:
                    result.errors.append(
                        "Declared README files must be of same type: found"
                        f" {', '.join(sorted(readme_types))}"
                    )

        return result

    def to_package(self, root: Path, with_groups: bool = True) -> ProjectPackage:
        from poetry.core.packages.dependency import Dependency
        from poetry.core.packages.dependency_group import MAIN_GROUP
        from poetry.core.packages.dependency_group import DependencyGroup
        from poetry.core.spdx.helpers import license_by_id

        config = self._content["tool"]["poetry"]

        package = ProjectPackage(config["name"], config["version"])
        package.root_dir = root

        for author in config.get("authors", []):
            package.authors.append(combine_unicode(author))

        for maintainer in config.get("maintainers", []):
            package.maintainers.append(combine_unicode(maintainer))

        package.description = config["description"]
        package.homepage = config.get("homepage")
        package.repository_url = config.get("repository")
        package.documentation_url = config.get("documentation")
        try:
            license_: License | None = license_by_id(config.get("license"))
        except ValueError:
            license_ = None

        package.license = license_
        package.keywords = config.get("keywords", [])
        package.classifiers = config.get("classifiers", [])

        if "readme" in config:
            if isinstance(config["readme"], str):
                package.readmes = (root / config["readme"],)
            else:
                package.readmes = tuple(root / readme for readme in config["readme"])

        if "dependencies" in config:
            self._add_package_group_dependencies(
                package=package, group=MAIN_GROUP, dependencies=config["dependencies"]
            )

        if with_groups and "group" in config:
            for group_name, group_config in config["group"].items():
                group = DependencyGroup(
                    group_name, optional=group_config.get("optional", False)
                )
                self._add_package_group_dependencies(
                    package=package,
                    group=group,
                    dependencies=group_config["dependencies"],
                )

        if with_groups and "dev-dependencies" in config:
            self._add_package_group_dependencies(
                package=package, group="dev", dependencies=config["dev-dependencies"]
            )

        extras = config.get("extras", {})
        for extra_name, requirements in extras.items():
            extra_name = canonicalize_name(extra_name)
            package.extras[extra_name] = []

            # Checking for dependency
            for req in requirements:
                req = Dependency(req, "*")

                for dep in package.requires:
                    if dep.name == req.name:
                        dep.in_extras.append(extra_name)
                        package.extras[extra_name].append(dep)

        if "build" in config:
            build = config["build"]
            if not isinstance(build, dict):
                build = {"script": build}
            package.build_config = build or {}

        if "include" in config:
            package.include = []

            for include in config["include"]:
                if not isinstance(include, dict):
                    include = {"path": include}

                formats = include.get("format", [])
                if formats and not isinstance(formats, list):
                    formats = [formats]
                include["format"] = formats

                package.include.append(include)

        if "exclude" in config:
            package.exclude = config["exclude"]

        if "packages" in config:
            package.packages = config["packages"]

        # Custom urls
        if "urls" in config:
            package.custom_urls = config["urls"]

        package.scripts = config.get("scripts", {})
        package.entrypoints = config.get("plugins", {})

        return package

    @classmethod
    def _add_package_group_dependencies(
        cls,
        package: ProjectPackage,
        group: str | DependencyGroup,
        dependencies: DependencyConfig,
    ) -> None:
        from poetry.core.packages.dependency_group import MAIN_GROUP

        if isinstance(group, str):
            if package.has_dependency_group(group):
                group = package.dependency_group(group)
            else:
                from poetry.core.packages.dependency_group import DependencyGroup

                group = DependencyGroup(group)

        for name, constraints in dependencies.items():
            _constraints = (
                constraints if isinstance(constraints, list) else [constraints]
            )
            for _constraint in _constraints:
                if name.lower() == "python":
                    if group.name == MAIN_GROUP and isinstance(_constraint, str):
                        package.python_versions = _constraint
                    continue

                group.add_dependency(
                    cls.create_dependency(
                        name,
                        _constraint,
                        groups=[group.name],
                        root_dir=package.root_dir,
                    )
                )

        package.add_dependency_group(group)

    @classmethod
    def create_dependency(
        cls,
        name: str,
        constraint: DependencyConstraint,
        groups: list[str] | None = None,
        root_dir: Path | None = None,
    ) -> Dependency:
        from pathlib import Path

        from poetry.core.packages.constraints import (
            parse_constraint as parse_generic_constraint,
        )
        from poetry.core.packages.dependency import Dependency
        from poetry.core.packages.dependency_group import MAIN_GROUP
        from poetry.core.packages.directory_dependency import DirectoryDependency
        from poetry.core.packages.file_dependency import FileDependency
        from poetry.core.packages.url_dependency import URLDependency
        from poetry.core.packages.utils.utils import create_nested_marker
        from poetry.core.packages.vcs_dependency import VCSDependency
        from poetry.core.semver.helpers import parse_constraint
        from poetry.core.version.markers import AnyMarker
        from poetry.core.version.markers import parse_marker

        if groups is None:
            groups = [MAIN_GROUP]

        if constraint is None:
            constraint = "*"

        if isinstance(constraint, dict):
            optional = constraint.get("optional", False)
            python_versions = constraint.get("python")
            platform = constraint.get("platform")
            markers = constraint.get("markers")

            allows_prereleases = constraint.get("allow-prereleases", False)

            dependency: Dependency
            if "git" in constraint:
                # VCS dependency
                dependency = VCSDependency(
                    name,
                    "git",
                    constraint["git"],
                    branch=constraint.get("branch", None),
                    tag=constraint.get("tag", None),
                    rev=constraint.get("rev", None),
                    directory=constraint.get("subdirectory", None),
                    groups=groups,
                    optional=optional,
                    develop=constraint.get("develop", False),
                    extras=constraint.get("extras", []),
                )
            elif "file" in constraint:
                file_path = Path(constraint["file"])

                dependency = FileDependency(
                    name,
                    file_path,
                    directory=constraint.get("subdirectory", None),
                    groups=groups,
                    base=root_dir,
                    extras=constraint.get("extras", []),
                )
            elif "path" in constraint:
                path = Path(constraint["path"])

                if root_dir:
                    is_file = root_dir.joinpath(path).is_file()
                else:
                    is_file = path.is_file()

                if is_file:
                    dependency = FileDependency(
                        name,
                        path,
                        directory=constraint.get("subdirectory", None),
                        groups=groups,
                        optional=optional,
                        base=root_dir,
                        extras=constraint.get("extras", []),
                    )
                else:
                    subdirectory = constraint.get("subdirectory", None)
                    if subdirectory:
                        path = path / subdirectory

                    dependency = DirectoryDependency(
                        name,
                        path,
                        groups=groups,
                        optional=optional,
                        base=root_dir,
                        develop=constraint.get("develop", False),
                        extras=constraint.get("extras", []),
                    )
            elif "url" in constraint:
                dependency = URLDependency(
                    name,
                    constraint["url"],
                    directory=constraint.get("subdirectory", None),
                    groups=groups,
                    optional=optional,
                    extras=constraint.get("extras", []),
                )
            else:
                version = constraint["version"]

                dependency = Dependency(
                    name,
                    version,
                    optional=optional,
                    groups=groups,
                    allows_prereleases=allows_prereleases,
                    extras=constraint.get("extras", []),
                )

            marker = parse_marker(markers) if markers else AnyMarker()

            if python_versions:
                marker = marker.intersect(
                    parse_marker(
                        create_nested_marker(
                            "python_version", parse_constraint(python_versions)
                        )
                    )
                )

            if platform:
                marker = marker.intersect(
                    parse_marker(
                        create_nested_marker(
                            "sys_platform", parse_generic_constraint(platform)
                        )
                    )
                )

            if not marker.is_any():
                dependency.marker = marker

            dependency.source_name = constraint.get("source")
        else:
            dependency = Dependency(name, constraint, groups=groups)

        return dependency

    @property
    def hash_content(self) -> dict[str, Any]:
        legacy_keys = ["dependencies", "source", "extras", "dev-dependencies"]
        relevant_keys = [*legacy_keys, "group"]

        config = self._content["tool"]["poetry"]

        hash_content: dict[str, Any] = {}

        for key in relevant_keys:
            data = config.get(key)

            if data is None and key not in legacy_keys:
                continue

            hash_content[key] = data

        return hash_content

    @property
    def poetry_config(self) -> dict[str, Any]:
        """
        The custom poetry configuration
        (i.e. the parts in [tool.poetry] that are not related to the package)
        """
        relevant_keys: list[str] = ["packages", "include", "exclude", "source"]

        config = self._content["tool"]["poetry"]
        poetry_config = {}

        for key in relevant_keys:
            if key in config:
                poetry_config[key] = config[key]

        return poetry_config
