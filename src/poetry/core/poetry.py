from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Optional


if TYPE_CHECKING:
    from pathlib import Path

    from poetry.core.lock.locker import Locker
    from poetry.core.packages.project_package import ProjectPackage
    from poetry.core.pyproject.toml import PyProjectTOML
    from poetry.core.toml import TOMLFile


class Poetry:
    def __init__(
        self,
        file: "Path",
        local_config: Dict[str, Any],
        package: "ProjectPackage",
    ) -> None:
        from poetry.core.pyproject.toml import PyProjectTOML

        self._pyproject = PyProjectTOML(file)
        self._package = package
        self._local_config = local_config
        self._locker: Optional["Locker"] = None

    @property
    def pyproject(self) -> "PyProjectTOML":
        return self._pyproject

    @property
    def file(self) -> "TOMLFile":
        return self._pyproject.file

    @property
    def package(self) -> "ProjectPackage":
        return self._package

    @property
    def local_config(self) -> Dict[str, Any]:
        return self._local_config

    def get_project_config(self, config: str, default: Any = None) -> Any:
        return self._local_config.get("config", {}).get(config, default)

    @property
    def locker(self) -> Optional["Locker"]:
        if self._locker is None:
            from poetry.core.lock.locker import Locker

            self._locker = Locker(
                self.pyproject.file.path.parent / "poetry.lock", self.local_config
            )
        return self._locker
