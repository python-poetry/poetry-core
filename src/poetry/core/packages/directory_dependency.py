from __future__ import annotations

import functools

from pathlib import Path
from typing import Iterable
from warnings import warn

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.utils.utils import is_python_project
from poetry.core.packages.utils.utils import path_to_url
from poetry.core.pyproject.toml import PyProjectTOML


class DirectoryDependency(Dependency):
    _full_path: Path | None

    def __init__(
        self,
        name: str,
        path: Path,
        groups: Iterable[str] | None = None,
        optional: bool = False,
        base: Path | None = None,
        develop: bool = False,
        extras: Iterable[str] | None = None,
    ) -> None:
        self._path = path
        self._base = base or Path.cwd()
        self._full_path = None
        self._develop = develop

        full_path = self._get_full_path(False, name)

        super().__init__(
            name,
            "*",
            groups=groups,
            optional=optional,
            allows_prereleases=True,
            source_type="directory",
            source_url=full_path.as_posix(),
            extras=extras,
        )
        # cache this function to avoid multiple IO reads and parsing
        self.supports_poetry = functools.lru_cache(maxsize=1)(self._supports_poetry)

    def _get_full_path(self, raise_if_invalid: bool, name: str) -> Path:
        if self._full_path is not None:
            return self._full_path
        full_path = self._path
        if not self._path.is_absolute():
            try:
                full_path = self._base.joinpath(self._path).resolve()
            except FileNotFoundError:
                msg = f"Source directory {self._path} for {name} does not exist"
                if raise_if_invalid:
                    raise ValueError(msg)
                warn(msg, category=UserWarning)
                return full_path

        if not full_path.exists():
            msg = f"Source directory {self._path} for {name} does not exist"
            if raise_if_invalid:
                raise ValueError(msg)
            warn(msg, category=UserWarning)
            return full_path

        if full_path.is_file():
            raise ValueError(
                f"Expected source for {name} to be a"
                f" directory but {self._path} is a file"
            )

        if not is_python_project(full_path):
            raise ValueError(
                f"The source directory {self._full_path} for {name}"
                " does not seem to be a Python package",
            )

        self._full_path = full_path
        return full_path

    @property
    def path(self) -> Path:
        return self._path

    @property
    def full_path(self) -> Path:
        return self._get_full_path(True, self.name)

    @property
    def base(self) -> Path:
        return self._base

    @property
    def develop(self) -> bool:
        return self._develop

    def _supports_poetry(self) -> bool:
        return PyProjectTOML(self.full_path / "pyproject.toml").is_poetry_project()

    def is_directory(self) -> bool:
        return True

    @property
    def base_pep_508_name(self) -> str:
        requirement = self.pretty_name

        if self.extras:
            extras = ",".join(sorted(self.extras))
            requirement += f"[{extras}]"

        path = path_to_url(self.full_path)
        requirement += f" @ {path}"

        return requirement
