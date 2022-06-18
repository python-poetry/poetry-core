from __future__ import annotations

import os
import re

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from tomlkit import loads
from tomlkit.toml_file import TOMLFile as BaseTOMLFile


if TYPE_CHECKING:
    from tomlkit.toml_document import TOMLDocument


class PatchedBaseTOMLFile(BaseTOMLFile):  # type: ignore[misc]
    """
    This class can be removed when https://github.com/sdispater/tomlkit/issues/200 is
    resolved and changes from https://github.com/sdispater/tomlkit/pull/201 are
    available.
    """

    def __init__(self, path: str) -> None:
        super().__init__(path)
        self._linesep = os.linesep

    def read(self) -> TOMLDocument:
        """Read the file content as a :class:`tomlkit.toml_document.TOMLDocument`."""
        with open(self._path, encoding="utf-8", newline="") as f:
            content = f.read()

            # check if consistent line endings
            num_newline = content.count("\n")
            if num_newline > 0:
                num_win_eol = content.count("\r\n")
                if num_win_eol == num_newline:
                    self._linesep = "\r\n"
                elif num_win_eol == 0:
                    self._linesep = "\n"
                else:
                    self._linesep = "mixed"

            return loads(content)

    def write(self, data: TOMLDocument) -> None:
        """Write the TOMLDocument to the file."""
        content = data.as_string()

        # apply linesep
        if self._linesep == "\n":
            content = content.replace("\r\n", "\n")
        elif self._linesep == "\r\n":
            content = re.sub(r"(?<!\r)\n", "\r\n", content)

        with open(self._path, "w", encoding="utf-8", newline="") as f:
            f.write(content)


class TOMLFile(PatchedBaseTOMLFile):
    def __init__(self, path: str | Path) -> None:
        if isinstance(path, str):
            path = Path(path)
        super().__init__(path.as_posix())
        self.__path = path

    @property
    def path(self) -> Path:
        return self.__path

    def exists(self) -> bool:
        return self.__path.exists()

    def read(self) -> TOMLDocument:
        from tomlkit.exceptions import TOMLKitError

        from poetry.core.toml import TOMLError

        try:
            return super().read()
        except (ValueError, TOMLKitError) as e:
            raise TOMLError(f"Invalid TOML file {self.path.as_posix()}: {e}")

    def __getattr__(self, item: str) -> Any:
        return getattr(self.__path, item)

    def __str__(self) -> str:
        return self.__path.as_posix()
