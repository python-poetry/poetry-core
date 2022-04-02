from __future__ import annotations

import contextlib

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.directory_dependency import DirectoryDependency
from poetry.core.packages.file_dependency import FileDependency
from poetry.core.utils.helpers import canonicalize_name


if TYPE_CHECKING:
    from poetry.core.packages.project_package import ProjectPackage
    from poetry.core.pyproject.toml import PyProjectTOML
    from poetry.core.toml import TOMLFile


class Poetry:
    def __init__(
        self,
        file: Path,
        local_config: dict[str, Any],
        package: ProjectPackage,
    ) -> None:
        from poetry.core.pyproject.toml import PyProjectTOML

        self._pyproject = PyProjectTOML(file)
        self._package = package
        self._local_config = local_config
        self._build_system_dependencies: list[Dependency] | None = None

    @property
    def pyproject(self) -> PyProjectTOML:
        return self._pyproject

    @property
    def file(self) -> TOMLFile:
        return self._pyproject.file

    @property
    def package(self) -> ProjectPackage:
        return self._package

    @property
    def local_config(self) -> dict[str, Any]:
        return self._local_config

    def get_project_config(self, config: str, default: Any = None) -> Any:
        return self._local_config.get("config", {}).get(config, default)

    @property
    def build_system_dependencies(self) -> list[Dependency]:
        if self._build_system_dependencies is None:
            build_system = self.pyproject.build_system
            self._build_system_dependencies = []

            for requirement in build_system.requires:
                dependency = None
                try:
                    dependency = Dependency.create_from_pep_508(requirement)
                except ValueError:
                    # PEP 517 requires can be path if not PEP 508
                    path = Path(requirement)

                    with contextlib.suppress(OSError):
                        # suppress OSError for compatibility with Python < 3.8
                        # https://docs.python.org/3/library/pathlib.html#methods
                        if path.is_file():
                            dependency = FileDependency(
                                name=canonicalize_name(path.name), path=path
                            )
                        elif path.is_dir():
                            dependency = DirectoryDependency(
                                name=canonicalize_name(path.name), path=path
                            )

                # skip since we could not determine requirement
                if dependency:
                    self._build_system_dependencies.append(dependency)

        return self._build_system_dependencies
