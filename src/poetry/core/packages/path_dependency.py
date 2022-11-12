from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Iterable

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.utils.utils import path_to_url


class PathDependency(Dependency, ABC):
    @abstractmethod
    def __init__(
        self,
        name: str,
        path: Path,
        *,
        source_type: str,
        groups: Iterable[str] | None = None,
        optional: bool = False,
        base: Path | None = None,
        extras: Iterable[str] | None = None,
    ) -> None:
        assert source_type in ("file", "directory")
        self._path = path
        self._base = base or Path.cwd()
        self._full_path = path

        if not self._path.is_absolute():
            try:
                self._full_path = self._base.joinpath(self._path).resolve()
            except FileNotFoundError:
                raise ValueError(f"Path {self._path} does not exist")

        if not self._full_path.exists():
            raise ValueError(f"Path {self._path} does not exist")

        super().__init__(
            name,
            "*",
            groups=groups,
            optional=optional,
            allows_prereleases=True,
            source_type=source_type,
            source_url=self._full_path.as_posix(),
            extras=extras,
        )

    @property
    def path(self) -> Path:
        return self._path

    @property
    def full_path(self) -> Path:
        return self._full_path

    @property
    def base(self) -> Path:
        return self._base

    def is_file(self) -> bool:
        return self._source_type == "file"

    def is_directory(self) -> bool:
        return self._source_type == "directory"

    @property
    def base_pep_508_name(self) -> str:
        requirement = self.pretty_name

        if self.extras:
            extras = ",".join(sorted(self.extras))
            requirement += f"[{extras}]"

        path = path_to_url(self.full_path)
        requirement += f" @ {path}"

        return requirement
