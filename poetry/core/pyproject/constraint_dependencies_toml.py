import os
import urllib.request

from tempfile import mkstemp
from typing import TYPE_CHECKING
from urllib.error import URLError
from urllib.parse import urlparse


if TYPE_CHECKING:
    from tomlkit.container import Container


class ConstraintDependenciesTOML:
    def __init__(self, path_or_url: str) -> None:
        self._path_or_url = path_or_url

    @property
    def dependencies(self) -> "Container":
        from tomlkit.exceptions import NonExistentKey

        from poetry.core.toml import TOMLFile

        url = (
            self._path_or_url
            if urlparse(self._path_or_url).scheme != ""
            else "file:" + self._path_or_url
        )
        try:
            content = urllib.request.urlopen(url).read()
        except URLError as e:
            raise RuntimeError(
                "Poetry could not load constraint dependencies file {}".format(
                    self._path_or_url
                )
            ) from e
        else:
            fd, path = mkstemp(prefix="poetry-constraint-dependencies-")
            with open(path, mode="w+b") as f:
                f.write(content)

            constraint_dependencies_file = TOMLFile(f.name)

            try:
                data = constraint_dependencies_file.read()

                try:
                    return data["poetry"]["constraint-dependencies"]
                except NonExistentKey as e:
                    raise RuntimeError(
                        "[poetry.constraint-dependencies] section not found in {}".format(
                            self._path_or_url
                        )
                    ) from e
            finally:
                os.close(fd)
                os.unlink(path)
