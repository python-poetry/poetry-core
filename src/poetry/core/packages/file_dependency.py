from __future__ import annotations

import hashlib
import io

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Iterable

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.utils.utils import path_to_url


if TYPE_CHECKING:
    from poetry.core.semver.version_constraint import VersionConstraint


class FileDependency(Dependency):
    def __init__(
        self,
        name: str,
        path: Path,
        groups: Iterable[str] | None = None,
        optional: bool = False,
        base: Path | None = None,
        extras: Iterable[str] | None = None,
    ) -> None:
        self._path = path
        self._base = base or Path.cwd()
        self._full_path = path

        if not self._path.is_absolute():
            try:
                self._full_path = self._base.joinpath(self._path).resolve()
            except FileNotFoundError:
                raise ValueError(f"Directory {self._path} does not exist")

        if not self._full_path.exists():
            raise ValueError(f"File {self._path} does not exist")

        if self._full_path.is_dir():
            raise ValueError(f"{self._path} is a directory, expected a file")

        super().__init__(
            name,
            "*",
            groups=groups,
            optional=optional,
            allows_prereleases=True,
            source_type="file",
            source_url=self._full_path.as_posix(),
            extras=extras,
        )

    @property
    def base(self) -> Path:
        return self._base

    @property
    def path(self) -> Path:
        return self._path

    @property
    def full_path(self) -> Path:
        return self._full_path

    def is_file(self) -> bool:
        return True

    def hash(self, hash_name: str = "sha256") -> str:
        h = hashlib.new(hash_name)
        with self._full_path.open("rb") as fp:
            for content in iter(lambda: fp.read(io.DEFAULT_BUFFER_SIZE), b""):
                h.update(content)

        return h.hexdigest()

    def with_constraint(self, constraint: str | VersionConstraint) -> FileDependency:
        new = FileDependency(
            self.pretty_name,
            path=self.path,
            base=self.base,
            optional=self.is_optional(),
            groups=list(self._groups),
            extras=list(self._extras),
        )

        new.set_constraint(constraint)
        new.is_root = self.is_root
        new.python_versions = self.python_versions
        new.marker = self.marker
        new.transitive_marker = self.transitive_marker

        for in_extra in self.in_extras:
            new.in_extras.append(in_extra)

        return new

    @property
    def base_pep_508_name(self) -> str:
        requirement = self.pretty_name

        if self.extras:
            extras = ",".join(sorted(self.extras))
            requirement += f"[{extras}]"

        path = path_to_url(self.path) if self.path.is_absolute() else self.path
        requirement += f" @ {path}"

        return requirement

    def __str__(self) -> str:
        if self.is_root:
            return self._pretty_name

        return f"{self._pretty_name} ({self._pretty_constraint} {self._path})"

    def __hash__(self) -> int:
        return hash((self._name, self._full_path))
