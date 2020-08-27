from __future__ import absolute_import
from __future__ import unicode_literals

from typing import TYPE_CHECKING
from typing import Any
from typing import Optional

from poetry.core.lock.locker import Locker
from poetry.core.pyproject import PyProjectTOML
from poetry.core.utils._compat import Path  # noqa


if TYPE_CHECKING:
    from poetry.core.masonry.metadata import MetadataConfig  # noqa
    from poetry.core.packages import ProjectPackage  # noqa
    from poetry.core.pyproject.toml import PyProjectTOMLFile  # noqa


class Poetry(object):
    def __init__(
        self, file, local_config, package, locker=None
    ):  # type: (Path, dict, "ProjectPackage", Optional[Locker]) -> None
        self._pyproject = PyProjectTOML(file)
        self._package = package
        self._local_config = local_config
        self._locker = locker or Locker(file.parent / "poetry.lock", local_config)
        self._build_metadata_config = None

    @property
    def pyproject(self):  # type: () -> PyProjectTOML
        return self._pyproject

    @property
    def file(self):  # type: () -> "PyProjectTOMLFile"
        return self._pyproject.file

    @property
    def package(self):  # type: () -> "ProjectPackage"
        return self._package

    @property
    def local_config(self):  # type: () -> dict
        return self._local_config

    @property
    def locker(self):  # type: () -> Optional[Locker]
        return self._locker

    @property
    def build_metadata_config(self):  # type: () -> "MetadataConfig"
        if self._build_metadata_config is None:
            from poetry.core.masonry.metadata import MetadataConfig  # noqa

            try:
                config = self._local_config.get("build", {}).get("metadata", {})
                dependency = config.get("dependencies", {})

                self._build_metadata_config = MetadataConfig(
                    dependency_lock=dependency.get("lock", False),
                    dependency_nested=dependency.get("nested", False),
                )
            except AttributeError:
                self._build_metadata_config = MetadataConfig()

        return self._build_metadata_config

    def get_project_config(self, config, default=None):  # type: (str, Any) -> Any
        return self._local_config.get("config", {}).get(config, default)
