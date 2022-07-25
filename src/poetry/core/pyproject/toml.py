from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from tomlkit.container import Container

from poetry.core.pyproject.formats.content_format import ContentFormat
from poetry.core.pyproject.formats.legacy_content_format import LegacyContentFormat


if TYPE_CHECKING:
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument

    from poetry.core.pyproject.tables import BuildSystem
    from poetry.core.toml import TOMLFile


class PyProjectTOML:
    SUPPORTED_FORMATS: list[type[ContentFormat]] = [LegacyContentFormat]

    def __init__(self, path: str | Path) -> None:
        from poetry.core.toml import TOMLFile

        self._file = TOMLFile(path=path)
        self._data: TOMLDocument | None = None
        self._content_format: ContentFormat | None = None
        self._build_system: BuildSystem | None = None

    @property
    def file(self) -> TOMLFile:
        return self._file

    @property
    def data(self) -> TOMLDocument:
        from tomlkit.toml_document import TOMLDocument

        if self._data is None:
            if not self._file.exists():
                self._data = TOMLDocument()
            else:
                self._data = self._file.read()
                self._content_format = self.guess_format(self._data)

        return self._data

    def is_build_system_defined(self) -> bool:
        return self._file.exists() and "build-system" in self.data

    @property
    def content_format(self) -> ContentFormat | None:
        return self.data and self._content_format

    @property
    def poetry_config(self) -> Container:
        if not self.is_poetry_project():
            from poetry.core.pyproject.exceptions import PyProjectException

            raise PyProjectException(f"{self._file} is not a Poetry pyproject file")

        return cast(ContentFormat, self._content_format).poetry_config

    @property
    def build_system(self) -> BuildSystem:
        from poetry.core.pyproject.tables import BuildSystem

        if self._build_system is None:
            build_backend = None
            requires = None

            if not self._file.exists():
                build_backend = "poetry.core.masonry.api"
                requires = ["poetry-core"]

            container = self.data.get("build-system", {})
            self._build_system = BuildSystem(
                build_backend=container.get("build-backend", build_backend),
                requires=container.get("requires", requires),
            )

        return self._build_system

    def is_poetry_project(self) -> bool:
        return self.data and self._content_format is not None

    def __getattr__(self, item: str) -> Any:
        return getattr(self.data, item)

    def save(self) -> None:
        from tomlkit.container import Container

        data = self.data

        if self._build_system is not None:
            if "build-system" not in data:
                data["build-system"] = Container()

            build_system = cast(Container, data["build-system"])
            build_system["requires"] = self._build_system.requires
            build_system["build-backend"] = self._build_system.build_backend

        self.file.write(data=data)

    def reload(self) -> None:
        self._data = None
        self._build_system = None
        self._content_format = None

    @classmethod
    def guess_format(cls, data: dict[str, Any]) -> ContentFormat | None:
        for fmt in cls.SUPPORTED_FORMATS:
            if fmt.supports(data):
                return fmt(data)

        return None
