from __future__ import annotations

import functools
import logging

from typing import TYPE_CHECKING
from typing import Iterable

from poetry.core.packages.path_dependency import PathDependency
from poetry.core.packages.utils.utils import is_python_project
from poetry.core.pyproject.toml import PyProjectTOML


if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class DirectoryDependency(PathDependency):
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
        super().__init__(
            name,
            path,
            source_type="directory",
            groups=groups,
            optional=optional,
            base=base,
            extras=extras,
        )
        self._develop = develop

        # cache this function to avoid multiple IO reads and parsing
        self.supports_poetry = functools.lru_cache(maxsize=1)(self._supports_poetry)

    @property
    def develop(self) -> bool:
        return self._develop

    def validate(self, *, raise_error: bool) -> bool:
        if not super().validate(raise_error=raise_error):
            return False

        message = ""
        if self._full_path.is_file():
            message = (
                f"{self._full_path} for {self.pretty_name} is a file,"
                " expected a directory"
            )
        elif not is_python_project(self._full_path):
            message = (
                f"Directory {self._full_path} for {self.pretty_name} does not seem"
                " to be a Python package"
            )

        if message:
            if raise_error:
                raise ValueError(message)
            logger.warning(message)
            return False
        return True

    def _supports_poetry(self) -> bool:
        return PyProjectTOML(self._full_path / "pyproject.toml").is_poetry_project()
