from typing import TYPE_CHECKING
from typing import List


if TYPE_CHECKING:
    from .types import DependencyTypes


class DependencyGroup:
    def __init__(self, name: str, optional: bool = False) -> None:
        self._name: str = name
        self._optional: bool = optional
        self._dependencies: List["DependencyTypes"] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def dependencies(self) -> List["DependencyTypes"]:
        return self._dependencies

    def is_optional(self) -> bool:
        return self._optional

    def add_dependency(self, dependency: "DependencyTypes") -> None:
        self._dependencies.append(dependency)

    def remove_dependency(self, name: "str") -> None:
        from poetry.core.utils.helpers import canonicalize_name

        name = canonicalize_name(name)

        dependencies = []
        for dependency in dependencies:
            if dependency.name == name:
                continue

            dependencies.append(dependency)

        self._dependencies = dependencies

    def __eq__(self, other: "DependencyGroup") -> bool:
        if not isinstance(other, DependencyGroup):
            return NotImplemented

        return self._name == other.name and set(self._dependencies) == set(
            other.dependencies
        )

    def __repr__(self) -> str:
        return "{}({}, optional={})".format(
            self.__class__.__name__, self._name, self._optional
        )
