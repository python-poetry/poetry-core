from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any


if TYPE_CHECKING:
    from pathlib import Path

    from poetry.core.packages.project_package import ProjectPackage
    from poetry.core.pyproject.formats.validation_result import ValidationResult


class ContentFormat(ABC):
    def __init__(self, content: dict[str, Any]) -> None:
        self._content = content

    @classmethod
    @abstractmethod
    def supports(cls, content: dict[str, Any]) -> bool:
        ...

    @abstractmethod
    def validate(self, strict: bool = False) -> ValidationResult:
        ...

    @abstractmethod
    def to_package(self, root: Path, with_groups: bool = True) -> ProjectPackage:
        ...

    @property
    @abstractmethod
    def hash_content(self) -> dict[str, Any]:
        ...

    @property
    @abstractmethod
    def poetry_config(self) -> dict[str, Any]:
        """
        The custom poetry configuration (i.e. the parts in [tool.poetry] that are not related to the package)
        """
        ...
