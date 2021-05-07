import urllib.request

from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING
from typing import Optional
from typing import Union
from urllib.error import URLError
from urllib.parse import urlparse


if TYPE_CHECKING:
    from tomlkit.container import Container
    from tomlkit.items import Item


class ConstraintDependenciesTOML:
    def __init__(self, path_or_url: str) -> None:
        self._path_or_url = path_or_url

    @property
    def dependencies(self) -> Optional[Union["Item", "Container"]]:
        from tomlkit.exceptions import NonExistentKey

        from poetry.core.toml import TOMLFile

        url = (
            self._path_or_url
            if urlparse(self._path_or_url).scheme != ""
            else "file:" + self._path_or_url
        )
        try:
            response = urllib.request.urlopen(url)
        except URLError as e:
            raise RuntimeError(
                "Poetry could not load constraint dependencies file {}".format(
                    self._path_or_url
                )
            ) from e
        else:
            with NamedTemporaryFile(
                prefix="poetry-constraint-dependencies-", buffering=0
            ) as fp:
                fp.write(response.read())
                constraint_dependencies_file = TOMLFile(fp.name)
                data = constraint_dependencies_file.read()

                try:
                    return data["poetry"]["constraint-dependencies"]
                except NonExistentKey as e:
                    raise RuntimeError(
                        "[poetry.constraint-dependencies] section not found in {}".format(
                            self._path_or_url
                        )
                    ) from e
