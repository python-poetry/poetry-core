from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Iterable


if TYPE_CHECKING:
    from poetry.core.semver.version_constraint import VersionConstraint

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.utils.utils import path_to_url


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
        from poetry.core.pyproject.toml import PyProjectTOML

        self._path = path
        self._base = base or Path.cwd()
        self._full_path = path

        if not self._path.is_absolute():
            try:
                self._full_path = self._base.joinpath(self._path).resolve()
            except FileNotFoundError:
                raise ValueError(f"Directory {self._path} does not exist")

        self._develop = develop
        self._supports_poetry = False

        if not self._full_path.exists():
            raise ValueError(f"Directory {self._path} does not exist")

        if self._full_path.is_file():
            raise ValueError(f"{self._path} is a file, expected a directory")

        # Checking content to determine actions
        setup = self._full_path / "setup.py"
        self._supports_poetry = PyProjectTOML(
            self._full_path / "pyproject.toml"
        ).is_poetry_project()

        if not setup.exists() and not self._supports_poetry:
            raise ValueError(
                f"Directory {self._full_path} does not seem to be a Python package"
            )

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

    def supports_poetry(self) -> bool:
        return self._supports_poetry

    def is_directory(self) -> bool:
        return True

    def with_constraint(
        self, constraint: str | VersionConstraint
    ) -> DirectoryDependency:
        new = DirectoryDependency(
            self.pretty_name,
            path=self.path,
            base=self.base,
            optional=self.is_optional(),
            groups=list(self._groups),
            develop=self._develop,
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

        path = self._path.as_posix()
        return f"{self._pretty_name} ({self._pretty_constraint} {path})"

    def __hash__(self) -> int:
        return hash((self._name, self._full_path.as_posix()))
