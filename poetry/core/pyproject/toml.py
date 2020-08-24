from typing import Optional
from typing import Union

from tomlkit.container import Container
from tomlkit.exceptions import TOMLKitError
from tomlkit.toml_document import TOMLDocument
from tomlkit.toml_file import TOMLFile

from poetry.core.pyproject.exceptions import PyProjectException
from poetry.core.pyproject.tables import BuildSystem
from poetry.core.utils._compat import Path


class PyProjectTOMLFile(TOMLFile):
    def __init__(self, path):  # type: (Union[str, Path]) -> None
        if isinstance(path, str):
            path = Path(path)
        super(PyProjectTOMLFile, self).__init__(path.as_posix())
        self.__path = path

    @property
    def path(self):  # type: () -> Path
        return self.__path

    def exists(self):  # type: () -> bool
        return self.__path.exists()

    def read(self):
        try:
            return super(PyProjectTOMLFile, self).read()
        except (ValueError, TOMLKitError) as e:
            raise PyProjectException(
                "Invalid TOML file {}: {}".format(self.path.as_posix(), e)
            )

    def __getattr__(self, item):
        return getattr(self.__path, item)

    def __str__(self):  # type: () -> str
        return self.__path.as_posix()


class PyProjectTOML:
    def __init__(self, path):  # type: (Union[str, Path]) -> None
        self._file = PyProjectTOMLFile(path=path)
        self._data = None  # type: Optional[TOMLDocument]
        self._build_system = None  # type: Optional[BuildSystem]
        self._poetry_config = None  # type: Optional[TOMLDocument]

    @property
    def file(self):  # type: () -> PyProjectTOMLFile
        return self._file

    @property
    def data(self):  # type: () -> TOMLDocument
        if self._data is None:
            self._data = self._file.read()
        return self._data

    @property
    def build_system(self):  # type: () -> BuildSystem
        if self._build_system is None:
            container = self.data.get("build-system", {})
            self._build_system = BuildSystem(
                build_backend=container.get("build-backend"),
                requires=container.get("requires"),
            )
        return self._build_system

    @property
    def poetry_config(self):  # type: () -> Optional[TOMLDocument]
        if self._poetry_config is None:
            self._poetry_config = self.data.get("tool", {}).get("poetry")
            if self._poetry_config is None:
                raise PyProjectException(
                    "[tool.poetry] section not found in {}".format(self._file)
                )
        return self._poetry_config

    def is_poetry_project(self):  # type: () -> bool
        if self.file.exists():
            try:
                _ = self.poetry_config
                return True
            except PyProjectException:
                pass
        return False

    def __getattr__(self, item):
        return getattr(self.data, item)

    def save(self):
        data = self.data

        if self._poetry_config is not None:
            data["tool"]["poetry"] = self._poetry_config

        if self._build_system is not None:
            if "build-system" not in data:
                data["build-system"] = Container()
            data["build-system"]["requires"] = self._build_system.requires
            data["build-system"]["build-backend"] = self._build_system.build_backend

        self.file.write(data=data)

    def reload(self):
        self._data = None
        self._build_system = None
        self._poetry_config = None
