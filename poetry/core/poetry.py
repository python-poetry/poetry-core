from __future__ import absolute_import
from __future__ import unicode_literals

from typing import Any

from .packages import ProjectPackage
from .pyproject import PyProjectTOMLFile
from .utils._compat import Path


class Poetry(object):
    def __init__(
        self, file, local_config, package,
    ):  # type: (Path, dict, ProjectPackage) -> None
        self._file = PyProjectTOMLFile(file)
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

    def get_project_config(self, config, default=None):  # type: (str, Any) -> Any
        return self._local_config.get("config", {}).get(config, default)
