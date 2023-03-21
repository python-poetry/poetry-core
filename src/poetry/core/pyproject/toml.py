from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any

from poetry.core.pyproject.tables import BuildSystem
from poetry.core.utils._compat import tomllib


class PyProjectTOML:
    def __init__(self, path: str | Path) -> None:
        self._file = path if isinstance(path, Path) else Path(path)
        self._data: dict[str, Any] | None = None
        self._build_system: BuildSystem | None = None

    @property
    def file(self) -> Path:
        return self._file

    @property
    def data(self) -> dict[str, Any]:
        if self._data is None:
            if not self.file.exists():
                self._data = {}
            else:
                with self.file.open("rb") as f:
                    self._data = tomllib.load(f)

        return self._data

    def is_build_system_defined(self) -> bool:
        return "build-system" in self.data

    @property
    def build_system(self) -> BuildSystem:
        if self._build_system is None:
            build_backend = None
            requires = None

            if not self.file.exists():
                build_backend = "poetry.core.masonry.api"
                requires = ["poetry-core"]

            container = self.data.get("build-system", {})
            self._build_system = BuildSystem(
                build_backend=container.get("build-backend", build_backend),
                requires=container.get("requires", requires),
            )

        return self._build_system

    @property
    def poetry_config(self) -> dict[str, Any]:
        try:
            tool = self.data["tool"]
            assert isinstance(tool, dict)
            config = tool["poetry"]
            assert isinstance(config, dict)
            return config
        except KeyError as e:
            from poetry.core.pyproject.exceptions import PyProjectException

            raise PyProjectException(
                f"[tool.poetry] section not found in {self._file.as_posix()}"
            ) from e

    def is_poetry_project(self) -> bool:
        from poetry.core.pyproject.exceptions import PyProjectException

        if self.file.exists():
            with suppress(PyProjectException):
                _ = self.poetry_config
                return True

        return False
