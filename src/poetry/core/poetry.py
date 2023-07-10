from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any


if TYPE_CHECKING:
    from pathlib import Path

    from poetry.core.packages.project_package import ProjectPackage
    from poetry.core.pyproject.toml import PyProjectTOML


class Poetry:
    def __init__(
        self,
        file: Path,
        pyproject: PyProjectTOML,
        package: ProjectPackage,
    ) -> None:
        self._pyproject = pyproject
        self._package = package

    @property
    def pyproject(self) -> PyProjectTOML:
        return self._pyproject

    @property
    def pyproject_path(self) -> Path:
        return self._pyproject.path

    @property
    def package(self) -> ProjectPackage:
        return self._package

    @property
    def local_config(self) -> dict[str, Any]:
        return self._pyproject.poetry_config

    def get_project_config(self, config: str, default: Any = None) -> Any:
        return self._local_config.get("config", {}).get(config, default)
