from __future__ import annotations

import logging

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import Union
from warnings import warn

from packaging.utils import canonicalize_name

from poetry.core.pyproject.formats.content_format import ContentFormat
from poetry.core.utils.helpers import readme_content_type


if TYPE_CHECKING:
    from collections.abc import Mapping

    from poetry.core.packages.dependency import Dependency
    from poetry.core.packages.project_package import ProjectPackage
    from poetry.core.poetry import Poetry

    DependencyConstraint = Union[str, Dict[str, Any]]
    DependencyConfig = Mapping[
        str, Union[List[DependencyConstraint], DependencyConstraint]
    ]


logger = logging.getLogger(__name__)


class Factory:
    """
    Factory class to create various elements needed by Poetry.
    """

    def create_poetry(
        self, cwd: Path | None = None, with_groups: bool = True
    ) -> Poetry:
        from poetry.core.poetry import Poetry
        from poetry.core.pyproject.toml import PyProjectTOML

        poetry_file = self.locate(cwd)
        pyproject = PyProjectTOML(path=poetry_file)

        if not pyproject.is_poetry_project():
            raise RuntimeError(f"The project at {poetry_file} is not a Poetry project")

        content_format = pyproject.content_format
        assert isinstance(content_format, ContentFormat)

        # Checking validity
        check_result = content_format.validate(strict=False)
        if check_result.errors:
            message = ""
            for error in check_result.errors:
                message += f"  - {error}\n"

            raise RuntimeError("The Poetry configuration is invalid:\n" + message)

        # Load package
        package = content_format.to_package(
            root=poetry_file.parent, with_groups=with_groups
        )

        return Poetry(poetry_file, pyproject.poetry_config, package)

    @classmethod
    def get_package(cls, name: str, version: str) -> ProjectPackage:
        from poetry.core.packages.project_package import ProjectPackage

        return ProjectPackage(name, version)

    @classmethod
    def create_dependency(
        cls,
        name: str,
        constraint: DependencyConstraint,
        groups: list[str] | None = None,
        root_dir: Path | None = None,
    ) -> Dependency:
        from poetry.core.constraints.generic import (
            parse_constraint as parse_generic_constraint,
        )
        from poetry.core.constraints.version import (
            parse_constraint as parse_version_constraint,
        )
        from poetry.core.packages.dependency import Dependency
        from poetry.core.packages.dependency_group import MAIN_GROUP
        from poetry.core.packages.directory_dependency import DirectoryDependency
        from poetry.core.packages.file_dependency import FileDependency
        from poetry.core.packages.url_dependency import URLDependency
        from poetry.core.packages.utils.utils import create_nested_marker
        from poetry.core.packages.vcs_dependency import VCSDependency
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
            if "allows-prereleases" in constraint:
                message = (
                    f'The "{name}" dependency specifies '
                    'the "allows-prereleases" property, which is deprecated. '
                    'Use "allow-prereleases" instead.'
                )
                warn(message, DeprecationWarning, stacklevel=2)
                logger.warning(message)

            allows_prereleases = constraint.get(
                "allow-prereleases", constraint.get("allows-prereleases", False)
            )

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
                            "python_version", parse_version_constraint(python_versions)
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

    @classmethod
    def validate(
        cls, config: dict[str, Any], strict: bool = False
    ) -> dict[str, list[str]]:
        """
        Checks the validity of a configuration
        """
        from poetry.core.json import validate_object

        result: dict[str, list[str]] = {"errors": [], "warnings": []}
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
                            f'The "{name}" dependency specifies '
                            'the "allows-prereleases" property, which is deprecated. '
                            'Use "allow-prereleases" instead.'
                        )

            if "extras" in config:
                for extra_name, requirements in config["extras"].items():
                    extra_name = canonicalize_name(extra_name)

                    for req in requirements:
                        req_name = canonicalize_name(req)
                        for dependency in config.get("dependencies", {}):
                            dep_name = canonicalize_name(dependency)
                            if req_name == dep_name:
                                break
                        else:
                            result["errors"].append(
                                f'Cannot find dependency "{req}" for extra '
                                f'"{extra_name}" in main dependencies.'
                            )

            # Checking for scripts with extras
            if "scripts" in config:
                scripts = config["scripts"]
                config_extras = config.get("extras", {})

                for name, script in scripts.items():
                    if not isinstance(script, dict):
                        continue

                    extras = script.get("extras", [])
                    for extra in extras:
                        if extra not in config_extras:
                            result["errors"].append(
                                f'Script "{name}" requires extra "{extra}" which is not'
                                " defined."
                            )

            # Checking types of all readme files (must match)
            if "readme" in config and not isinstance(config["readme"], str):
                readme_types = {readme_content_type(r) for r in config["readme"]}
                if len(readme_types) > 1:
                    result["errors"].append(
                        "Declared README files must be of same type: found"
                        f" {', '.join(sorted(readme_types))}"
                    )

        return result

    @classmethod
    def locate(cls, cwd: Path | None = None) -> Path:
        cwd = Path(cwd or Path.cwd())
        candidates = [cwd]
        candidates.extend(cwd.parents)

        for path in candidates:
            poetry_file = path / "pyproject.toml"

            if poetry_file.exists():
                return poetry_file

        else:
            raise RuntimeError(
                f"Poetry could not find a pyproject.toml file in {cwd} or its parents"
            )
