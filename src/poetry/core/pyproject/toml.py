from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from poetry.core.pyproject.tables import BuildSystem
from poetry.core.utils._compat import tomllib


if TYPE_CHECKING:
    from pathlib import Path

    from poetry.core.pyproject.formats.content_format import ContentFormat


class PyProjectTOML:
    def __init__(
        self, path: Path, content_format: type[ContentFormat] | None = None
    ) -> None:
        if content_format is None:
            from poetry.core.pyproject.formats.legacy_content_format import (
                LegacyContentFormat,
            )

            content_format = LegacyContentFormat

        self._path = path
        self._content_format: type[ContentFormat] = content_format
        self._data: dict[str, Any] | None = None
        self._content: ContentFormat | None = None
        self._build_system: BuildSystem | None = None

    @property
    def path(self) -> Path:
        return self._path

    @property
    def data(self) -> dict[str, Any]:
        if self._data is None:
            if not self.path.exists():
                self._data = {}
            else:
                with self.path.open("rb") as f:
                    self._data = tomllib.load(f)

        return self._data

    @property
    def content(self) -> ContentFormat:
        if self._content is not None:
            return self._content

        self._content = self._content_format(self.data)

        return self._content

    def is_build_system_defined(self) -> bool:
        return "build-system" in self.data

    @property
    def build_system(self) -> BuildSystem:
        if self._build_system is None:
            build_backend = None
            requires = None

            if not self._path.exists():
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
        if not self.is_poetry_project():
            from poetry.core.pyproject.exceptions import PyProjectException

            raise PyProjectException(f"{self._path} is not a Poetry pyproject file")

        return self.content.poetry_config

    def is_poetry_project(self) -> bool:
        return not self.content.is_empty()
