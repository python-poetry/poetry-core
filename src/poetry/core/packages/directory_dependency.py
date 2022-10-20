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
        self._full_path = path
        self._develop = develop

        self._validate()

        super().__init__(
            name,
            "*",
            groups=groups,
            optional=optional,
            allows_prereleases=True,
            source_type="directory",
            source_url=self._full_path.as_posix(),
            extras=extras,
        )
        # cache this function to avoid multiple IO reads and parsing
        self.supports_poetry = functools.lru_cache(maxsize=1)(self._supports_poetry)

    def _validate(self) -> None:
        # If the directory exists do some general validation on it.
        # There is no valid reason to have a path dependency to something
        # that is not a valid Python project.
        # If the directory doesn't exist, emit a warning and continue.
        # The most common cause of a directory not existing is likely user error
        # (e.g. a typo) so we want to do _something_ to alert them.
        # But there are also valid situations where we might want to build
        # a directory dependency pointing to a non-existing folder, for example:
        # - We are re-locking a project where a path dependency was removed
        #   It still exists in the lockfile and once we finish re-locking 
        #   we'll delete it from the lockfile, but we need to load it from the
        #   lockfile first to begin solving.
        # - A user wants to dynamically link to / insert the dependency at runtime.
        #   This may seem a bit strange but in theory is totally valid and we should
        #   allow it.
        if not self._path.is_absolute():
            try:
                self._full_path = self._base.joinpath(self._path).resolve()
            except FileNotFoundError:
                warn(f"Directory {self._path} does not exist", category=UserWarning)
                return

        if not self._full_path.exists():
            warn(f"Directory {self._path} does not exist", category=UserWarning)
            return

        if self._full_path.is_file():
            raise ValueError(f"{self._path} is a file, expected a directory")

        if not is_python_project(self._full_path):
            raise ValueError(
                f"Directory {self._full_path} does not seem to be a Python package",
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

    @property
    def develop(self) -> bool:
        return self._develop

    def _supports_poetry(self) -> bool:
        return PyProjectTOML(self._full_path / "pyproject.toml").is_poetry_project()

    def is_directory(self) -> bool:
        return True

    @property
    def base_pep_508_name(self) -> str:
        requirement = self.pretty_name

        if self.extras:
            extras = ",".join(sorted(self.extras))
            requirement += f"[{extras}]"

        path = (
            path_to_url(self.path) if self.path.is_absolute() else self.path.as_posix()
        )
        requirement += f" @ {path}"

        return requirement
