from typing import Union

from tomlkit.exceptions import TOMLKitError
from tomlkit.toml_file import TOMLFile as BaseTOMLFile

from poetry.core.toml import TOMLError
from poetry.core.utils._compat import Path


class TOMLFile(BaseTOMLFile):
    def __init__(self, path):  # type: (Union[str, Path]) -> None
        if isinstance(path, str):
            path = Path(path)
        super(TOMLFile, self).__init__(path.as_posix())
        self.__path = path

    @property
    def path(self):  # type: () -> Path
        return self.__path

    def exists(self):  # type: () -> bool
        return self.__path.exists()

    def read(self):
        try:
            return super(TOMLFile, self).read()
        except (ValueError, TOMLKitError) as e:
            raise TOMLError("Invalid TOML file {}: {}".format(self.path.as_posix(), e))

    def __getattr__(self, item):
        return getattr(self.__path, item)

    def __str__(self):  # type: () -> str
        return self.__path.as_posix()
