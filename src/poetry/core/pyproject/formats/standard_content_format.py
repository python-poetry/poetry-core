from __future__ import annotations

from typing import TYPE_CHECKING

from packaging.utils import canonicalize_name

from poetry.core.json import validate_object
from poetry.core.packages.project_package import ProjectPackage
from poetry.core.pyproject.formats.content_format import ContentFormat
from poetry.core.pyproject.formats.validation_result import ValidationResult
from poetry.core.utils.helpers import combine_unicode


if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from poetry.core.packages.dependency_group import DependencyGroup
    from poetry.core.spdx.license import License


class StandardContentFormat(ContentFormat):
    @classmethod
    def supports(cls, content: dict[str, Any]) -> bool:
        return "project" in content

    def validate(self, strict: bool = False) -> ValidationResult:
        result = ValidationResult([], [])

        # Schema validation errors
        validation_errors = validate_object(self._content, "poetry-pep621-schema")

        result.errors += validation_errors

        return result

    def to_package(self, root: Path, with_groups: bool = True) -> ProjectPackage:
        from poetry.core.packages.dependency import Dependency
        from poetry.core.packages.dependency_group import MAIN_GROUP
        from poetry.core.spdx.helpers import license_by_id

        config = self._content["project"]

        package = ProjectPackage(config["name"], config["version"])
        package.root_dir = root

        if "requires-python" in config:
            package.python_versions = config["requires-python"]

        for author in config.get("authors", []):
            name, email = author.get("name"), author.get("email")
            if name and email:
                package.authors.append(
                    f"{combine_unicode(name)} <{combine_unicode(email)}>"
                )
            elif name:
                package.authors.append(combine_unicode(name))
            else:
                package.authors.append(combine_unicode(name))

        for maintainer in config.get("maintainers", []):
            name, email = maintainer.get("name"), maintainer.get("email")
            if name and email:
                package.maintainers.append(
                    f"{combine_unicode(name)} <{combine_unicode(email)}>"
                )
            elif name:
                package.maintainers.append(combine_unicode(name))
            else:
                package.maintainers.append(combine_unicode(name))

        package.description = config.get("description")

        if "text" in config.get("license", {}):
            try:
                license_: License | None = license_by_id(config["license"]["text"])
            except ValueError:
                license_ = None
        else:
            license_ = None

        package.license = license_
        package.keywords = config.get("keywords", [])
        package.classifiers = config.get("classifiers", [])

        if "readme" in config:
            readme = config["readme"]
            if isinstance(readme, str):
                package.readme = root / readme
            elif "file" in readme:
                package.readme = root / readme["file"]
                package.readme_content_type = readme["content-type"]
            elif "text" in readme:
                package.readme_content = root / readme["text"]
                package.readme_content_type = readme["content-type"]

        if "dependencies" in config:
            self._add_package_group_dependencies(
                package, MAIN_GROUP, config["dependencies"], root_dir=root
            )

        if "optional-dependencies" in config:
            for extra_name, dependencies in config["optional-dependencies"].items():
                extra_name = canonicalize_name(extra_name)
                package.extras[extra_name] = []

                for dependency_constraint in dependencies:
                    dependency = Dependency.create_from_pep_508(
                        dependency_constraint, relative_to=root
                    )
                    dependency._optional = True
                    dependency.in_extras.append(extra_name)
                    package.extras[extra_name].append(dependency)

                    if not package.has_dependency_group(MAIN_GROUP):
                        group = DependencyGroup(MAIN_GROUP)
                        package.add_dependency_group(group)
                    else:
                        group = package.dependency_group(MAIN_GROUP)

                    group.add_dependency(dependency)

        # Custom urls
        if "urls" in config:
            package.custom_urls = config["urls"]

        package.scripts = config.get("scripts", {})
        package.gui_scripts = config.get("gui-scripts", {})
        package.entrypoints = config.get("entry-points", {})

        poetry_config = config.get("tool", {}).get("poetry", {})

        if "build" in poetry_config:
            build = poetry_config["build"]
            if not isinstance(build, dict):
                build = {"script": build}
            package.build_config = build or {}

        if "include" in poetry_config:
            package.include = []

            for include in poetry_config["include"]:
                if not isinstance(include, dict):
                    include = {"path": include}

                formats = include.get("format", [])
                if formats and not isinstance(formats, list):
                    formats = [formats]
                include["format"] = formats

                package.include.append(include)

        if "exclude" in poetry_config:
            package.exclude = poetry_config["exclude"]

        if "packages" in poetry_config:
            package.packages = poetry_config["packages"]

        return package

    @property
    def hash_content(self) -> dict[str, Any]:
        project_keys = ["dependencies", "optional-dependencies"]
        poetry_keys = ["source", "group"]

        hash_content: dict[str, Any] = {}

        for key in project_keys:
            data = self._content["project"].get(key)

            if data is None:
                continue

            hash_content[f"project.{key}"] = data

        poetry_config = self.poetry_config
        for key in poetry_keys:
            data = poetry_config.get(key)

            if data is None:
                continue

            hash_content[f"poetry.{key}"] = data

        return hash_content

    @property
    def poetry_config(self) -> dict[str, Any]:
        """
        The custom poetry configuration (i.e. the parts in [tool.poetry] that are not related to the package)
        """
        relevant_keys: list[str] = ["packages", "include", "exclude", "source"]

        config = self._content["tool"]["poetry"]
        poetry_config = {}

        for key in relevant_keys:
            if key in config:
                poetry_config[key] = config[key]

        return poetry_config

    @classmethod
    def _add_package_group_dependencies(
        cls,
        package: ProjectPackage,
        group: str | DependencyGroup,
        dependencies: list[str],
        root_dir: Path | None = None,
    ) -> None:
        from poetry.core.packages.dependency import Dependency

        if isinstance(group, str):
            if package.has_dependency_group(group):
                group = package.dependency_group(group)
            else:
                from poetry.core.packages.dependency_group import DependencyGroup

                group = DependencyGroup(group)

        for constraint in dependencies:
            dependency = Dependency.create_from_pep_508(
                constraint, relative_to=root_dir
            )
            group.add_dependency(dependency)

        package.add_dependency_group(group)
