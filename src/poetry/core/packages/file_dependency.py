from __future__ import annotations

import hashlib
import io

from pathlib import Path
from typing import Iterable
from warnings import warn

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.utils.utils import path_to_url


class FileDependency(Dependency):
    _full_path: Path | None

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
        self._full_path = None
        full_path = self._get_full_path(False, name)

        super().__init__(
            name,
            "*",
            groups=groups,
            optional=optional,
            allows_prereleases=True,
            source_type="file",
            source_url=full_path.as_posix(),
            extras=extras,
        )

    def _get_full_path(self, raise_if_invalid: bool, name: str) -> Path:
        if self._full_path is not None:
            return self._full_path
        full_path = self._path
        if not self._path.is_absolute():
            try:
                full_path = self._base.joinpath(self._path).resolve()
            except FileNotFoundError:
                msg = f"Source file {self._path} for {name} does not exist"
                if raise_if_invalid:
                    raise ValueError(msg)
                warn(msg, category=UserWarning)
                return full_path

        if not full_path.exists():
            msg = f"Source file {self._path} for {name} does not exist"
            if raise_if_invalid:
                raise ValueError(msg)
            warn(msg, category=UserWarning)
            return full_path

        if full_path.is_dir():
            raise ValueError(
                f"Expected source for {name} to be a"
                f" file but {self._path} is a directory"
            )

        self._full_path = full_path
        return full_path

    @property
    def base(self) -> Path:
        return self._base

    @property
    def path(self) -> Path:
        return self._path

    @property
    def full_path(self) -> Path:
        return self._get_full_path(True, self.name)

    def is_file(self) -> bool:
        return True

    def hash(self, hash_name: str = "sha256") -> str:
        h = hashlib.new(hash_name)
        with self.full_path.open("rb") as fp:
            for content in iter(lambda: fp.read(io.DEFAULT_BUFFER_SIZE), b""):
                h.update(content)

        return h.hexdigest()

    @property
    def base_pep_508_name(self) -> str:
        requirement = self.pretty_name

        if self.extras:
            extras = ",".join(sorted(self.extras))
            requirement += f"[{extras}]"

        path = path_to_url(self.full_path)
        requirement += f" @ {path}"

        return requirement
