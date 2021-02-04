from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Optional
from typing import Union


if TYPE_CHECKING:
    from tomlkit.toml_document import TOMLDocument

    from poetry.core.toml import TOMLFile

    from .tables import BuildSystem


class PyProjectTOML:
    def __init__(self, path: Union[str, Path]) -> None:
        from poetry.core.toml import TOMLFile

        self._file = TOMLFile(path=path)
        self._data: Optional["TOMLDocument"] = None
        self._build_system: Optional["BuildSystem"] = None
        self._poetry_config: Optional["TOMLDocument"] = None

    @property
    def file(self) -> "TOMLFile":
        return self._file

    @property
    def data(self) -> "TOMLDocument":
        from tomlkit.toml_document import TOMLDocument

        if self._data is None:
            if not self._file.exists():
                self._data = TOMLDocument()
            else:
                self._data = self._file.read()

        return self._data

    @property
    def build_system(self) -> "BuildSystem":
        from .tables import BuildSystem

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

    @property
    def poetry_config(self) -> Optional["TOMLDocument"]:
        from .exceptions import PyProjectException

        if self._poetry_config is None:
            self._poetry_config = self.data.get("tool", {}).get("poetry")
            if self._poetry_config is None:
                raise PyProjectException(
                    "[tool.poetry] section not found in {}".format(self._file)
                )

        return self._poetry_config

    def is_poetry_project(self) -> bool:
        from .exceptions import PyProjectException

        if self.file.exists():
            try:
                _ = self.poetry_config
                return True
            except PyProjectException:
                pass

        return False

    def __getattr__(self, item: str) -> Any:
        return getattr(self.data, item)

    def save(self) -> None:
        from tomlkit.container import Container

        data = self.data

        if self._poetry_config is not None:
            data["tool"]["poetry"] = self._poetry_config

        if self._build_system is not None:
            if "build-system" not in data:
                data["build-system"] = Container()

            data["build-system"]["requires"] = self._build_system.requires
            data["build-system"]["build-backend"] = self._build_system.build_backend

        self.file.write(data=data)

    def reload(self) -> None:
        self._data = None
        self._build_system = None
        self._poetry_config = None
