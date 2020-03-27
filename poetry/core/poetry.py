from __future__ import absolute_import
from __future__ import unicode_literals

from .packages import ProjectPackage
from .utils._compat import Path
from .utils.toml_file import TomlFile


class Poetry(object):
    def __init__(
        self, file, local_config, package,
    ):  # type: (Path, dict, ProjectPackage) -> None
        self._file = TomlFile(file)
        self._package = package
        self._local_config = local_config

    @property
    def file(self):
        return self._file

    @property
    def package(self):  # type: () -> ProjectPackage
        return self._package

    @property
    def local_config(self):  # type: () -> dict
        return self._local_config
