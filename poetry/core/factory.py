from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
from warnings import warn


if TYPE_CHECKING:
    from .packages.project_package import ProjectPackage
    from .packages.types import DependencyTypes
    from .poetry import Poetry

logger = logging.getLogger(__name__)


class Factory(object):
    """
    Factory class to create various elements needed by Poetry.
    """

    def create_poetry(
        self, cwd: Optional[Path] = None, with_groups: bool = True
    ) -> "Poetry":
        from .poetry import Poetry
        from .pyproject.toml import PyProjectTOML

        poetry_file = self.locate(cwd)
        local_config = PyProjectTOML(path=poetry_file).poetry_config

        # Checking validity
        check_result = self.validate(local_config)
        if check_result["errors"]:
            message = ""
            for error in check_result["errors"]:
                message += "  - {}\n".format(error)

            raise RuntimeError("The Poetry configuration is invalid:\n" + message)

        # Load package
        name = local_config["name"]
        version = local_config["version"]
        package = self.get_package(name, version)
        package = self.configure_package(
            package, local_config, poetry_file.parent, with_groups=with_groups
        )

        return Poetry(poetry_file, local_config, package)

    @classmethod
    def get_package(cls, name: str, version: str) -> "ProjectPackage":
        from .packages.project_package import ProjectPackage

        return ProjectPackage(name, version, version)

    @classmethod
    def configure_package(
        cls,
        package: "ProjectPackage",
        config: Dict[str, Any],
        root: Path,
        with_groups: bool = True,
    ) -> "ProjectPackage":
        from .packages.dependency import Dependency
        from .packages.dependency_group import DependencyGroup
        from .spdx.helpers import license_by_id

        package.root_dir = root

        for author in config["authors"]:
            package.authors.append(author)

        for maintainer in config.get("maintainers", []):
            package.maintainers.append(maintainer)

        package.description = config.get("description", "")
        package.homepage = config.get("homepage")
        package.repository_url = config.get("repository")
        package.documentation_url = config.get("documentation")
        try:
            license_ = license_by_id(config.get("license", ""))
        except ValueError:
            license_ = None

        package.license = license_
        package.keywords = config.get("keywords", [])
        package.classifiers = config.get("classifiers", [])

        if "readme" in config:
            package.readme = root / config["readme"]

        if "platform" in config:
            package.platform = config["platform"]

        if "dependencies" in config:
            group = DependencyGroup("default")
            for name, constraint in config["dependencies"].items():
                if name.lower() == "python":
                    package.python_versions = constraint
                    continue

                if isinstance(constraint, list):
                    for _constraint in constraint:
                        group.add_dependency(
                            cls.create_dependency(
                                name, _constraint, root_dir=package.root_dir
                            )
                        )

                    continue

                group.add_dependency(
                    cls.create_dependency(name, constraint, root_dir=package.root_dir)
                )

            package.add_dependency_group(group)

        if with_groups and "group" in config:
            for group_name, group_config in config["group"].items():
                group = DependencyGroup(
                    group_name, optional=group_config.get("optional", False)
                )
                for name, constraint in group_config["dependencies"].items():
                    if isinstance(constraint, list):
                        for _constraint in constraint:
                            group.add_dependency(
                                cls.create_dependency(
                                    name,
                                    _constraint,
                                    groups=[group_name],
                                    root_dir=package.root_dir,
                                )
                            )

                        continue

                    group.add_dependency(
                        cls.create_dependency(
                            name,
                            constraint,
                            groups=[group_name],
                            root_dir=package.root_dir,
                        )
                    )

                package.add_dependency_group(group)

        if with_groups and "dev-dependencies" in config:
            group = DependencyGroup("dev")
            for name, constraint in config["dev-dependencies"].items():
                if isinstance(constraint, list):
                    for _constraint in constraint:
                        group.add_dependency(
                            cls.create_dependency(
                                name,
                                _constraint,
                                groups=["dev"],
                                root_dir=package.root_dir,
                            )
                        )

                    continue

                group.add_dependency(
                    cls.create_dependency(
                        name, constraint, groups=["dev"], root_dir=package.root_dir
                    )
                )

            package.add_dependency_group(group)

        extras = config.get("extras", {})
        for extra_name, requirements in extras.items():
            package.extras[extra_name] = []

            # Checking for dependency
            for req in requirements:
                req = Dependency(req, "*")

                for dep in package.requires:
                    if dep.name == req.name:
                        dep.in_extras.append(extra_name)
                        package.extras[extra_name].append(dep)

                        break

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

        return package

    @classmethod
    def create_dependency(
        cls,
        name: str,
        constraint: Union[str, Dict[str, Any]],
        groups: Optional[List[str]] = None,
        root_dir: Optional[Path] = None,
    ) -> "DependencyTypes":
        from .packages.constraints import parse_constraint as parse_generic_constraint
        from .packages.dependency import Dependency
        from .packages.directory_dependency import DirectoryDependency
        from .packages.file_dependency import FileDependency
        from .packages.url_dependency import URLDependency
        from .packages.utils.utils import create_nested_marker
        from .packages.vcs_dependency import VCSDependency
        from .version.markers import AnyMarker
        from .version.markers import parse_marker

        if groups is None:
            groups = ["default"]

        if constraint is None:
            constraint = "*"

        if isinstance(constraint, dict):
            optional = constraint.get("optional", False)
            python_versions = constraint.get("python")
            platform = constraint.get("platform")
            markers = constraint.get("markers")
            if "allows-prereleases" in constraint:
                message = (
                    'The "{}" dependency specifies '
                    'the "allows-prereleases" property, which is deprecated. '
                    'Use "allow-prereleases" instead.'.format(name)
                )
                warn(message, DeprecationWarning)
                logger.warning(message)

            allows_prereleases = constraint.get(
                "allow-prereleases", constraint.get("allows-prereleases", False)
            )

            if "git" in constraint:
                # VCS dependency
                dependency = VCSDependency(
                    name,
                    "git",
                    constraint["git"],
                    branch=constraint.get("branch", None),
                    tag=constraint.get("tag", None),
                    rev=constraint.get("rev", None),
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
                        groups=groups,
                        optional=optional,
                        base=root_dir,
                        extras=constraint.get("extras", []),
                    )
                else:
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

            if not markers:
                marker = AnyMarker()
                if python_versions:
                    dependency.python_versions = python_versions
                    marker = marker.intersect(
                        parse_marker(
                            create_nested_marker(
                                "python_version", dependency.python_constraint
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
            else:
                marker = parse_marker(markers)

            if not marker.is_any():
                dependency.marker = marker

            dependency.source_name = constraint.get("source")
        else:
            dependency = Dependency(name, constraint, groups=groups)

        return dependency

    @classmethod
    def validate(cls, config: dict, strict: bool = False) -> Dict[str, List[str]]:
        """
        Checks the validity of a configuration
        """
        from .json import validate_object

        result = {"errors": [], "warnings": []}
        # Schema validation errors
        validation_errors = validate_object(config, "poetry-schema")

        result["errors"] += validation_errors

        if strict:
            # If strict, check the file more thoroughly
            if "dependencies" in config:
                python_versions = config["dependencies"]["python"]
                if python_versions == "*":
                    result["warnings"].append(
                        "A wildcard Python dependency is ambiguous. "
                        "Consider specifying a more explicit one."
                    )

                for name, constraint in config["dependencies"].items():
                    if not isinstance(constraint, dict):
                        continue

                    if "allows-prereleases" in constraint:
                        result["warnings"].append(
                            'The "{}" dependency specifies '
                            'the "allows-prereleases" property, which is deprecated. '
                            'Use "allow-prereleases" instead.'.format(name)
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
                            result["errors"].append(
                                'Script "{}" requires extra "{}" which is not defined.'.format(
                                    name, extra
                                )
                            )

        return result

    @classmethod
    def locate(cls, cwd: Path) -> Path:
        candidates = [Path(cwd)]
        candidates.extend(Path(cwd).parents)

        for path in candidates:
            poetry_file = path / "pyproject.toml"

            if poetry_file.exists():
                return poetry_file

        else:
            raise RuntimeError(
                "Poetry could not find a pyproject.toml file in {} or its parents".format(
                    cwd
                )
            )
