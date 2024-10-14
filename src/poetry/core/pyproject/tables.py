from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from poetry.core.packages.dependency import Dependency


class BuildSystem:
    def __init__(
        self, build_backend: str | None = None, requires: list[str] | None = None
    ) -> None:
        self.build_backend = (
            build_backend
            if build_backend is not None
            else "setuptools.build_meta:__legacy__"
        )
        self.requires = requires if requires is not None else ["setuptools", "wheel"]

    @cached_property
    def dependencies(self) -> list[Dependency]:
        # avoid circular dependency when loading DirectoryDependency
        from poetry.core.packages.dependency import Dependency
        from poetry.core.packages.directory_dependency import DirectoryDependency
        from poetry.core.packages.file_dependency import FileDependency

        dependencies = []
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

            dependencies.append(dependency)

        return dependencies
