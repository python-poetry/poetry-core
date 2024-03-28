from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from poetry.core.packages.dependency import Dependency


@dataclass
class BuildSystem:
    build_backend: str | None = field(default=None)
    requires: list[str] = field(default_factory=list)
    _dependencies: list[Dependency] | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.build_backend = self.build_backend or "setuptools.build_meta:__legacy__"
        self.requires = self.requires or ["setuptools", "wheel"]

    @property
    def dependencies(self) -> list[Dependency]:
        if self._dependencies is None:
            # avoid circular dependency when loading DirectoryDependency
            from poetry.core.packages.dependency import Dependency
            from poetry.core.packages.directory_dependency import DirectoryDependency
            from poetry.core.packages.file_dependency import FileDependency

            self._dependencies = []
            for requirement in self.requires:
                dependency = None
                try:
                    dependency = Dependency.create_from_pep_508(requirement)
                except ValueError:
                    # PEP 517 requires can be path if not PEP 508
                    path = Path(requirement)
                    if path.is_file():
                        dependency = FileDependency(name=path.name, path=path)
                    elif path.is_dir():
                        dependency = DirectoryDependency(name=path.name, path=path)

                if dependency is None:
                    # skip since we could not determine requirement
                    continue

                self._dependencies.append(dependency)

        return self._dependencies
