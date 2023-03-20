from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from poetry.core.pyproject.formats.content_format import ContentFormat
from poetry.core.pyproject.formats.legacy_content_format import LegacyContentFormat
from poetry.core.pyproject.formats.standard_content_format import StandardContentFormat
from poetry.core.pyproject.tables import BuildSystem
from poetry.core.utils._compat import tomllib


if TYPE_CHECKING:
    from pathlib import Path


class PyProjectTOML:
    SUPPORTED_FORMATS: list[type[ContentFormat]] = [
        LegacyContentFormat,
        StandardContentFormat,
    ]

    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: dict[str, Any] | None = None
        self._content_format: ContentFormat | None = None
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

                self._content_format = self.guess_format(self._data)

        return self._data

    @property
    def content_format(self) -> ContentFormat | None:
        if self.data:
            return self._content_format

        return None

    def is_build_system_defined(self) -> bool:
        return "build-system" in self.data

    @property
    def build_system(self) -> BuildSystem:
        if self._build_system is None:
            build_backend = None
            requires = None

            if not self.path.exists():
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

        assert isinstance(self._content_format, ContentFormat)

        return self._content_format.poetry_config

    def is_poetry_project(self) -> bool:
        if not self.data:
            return False

        return self._content_format is not None

    @classmethod
    def guess_format(cls, data: dict[str, Any]) -> ContentFormat | None:
        for fmt in cls.SUPPORTED_FORMATS:
            if fmt.supports(data):
                return fmt(data)

        return None
