from typing import TYPE_CHECKING

from .version_constraint import VersionConstraint


if TYPE_CHECKING:
    from . import VersionTypes  # noqa
    from .version import Version  # noqa


class EmptyConstraint(VersionConstraint):
    def is_empty(self) -> bool:
        return True

    def is_any(self) -> bool:
        return False

    def allows(self, version: "Version") -> bool:
        return False

    def allows_all(self, other: "VersionTypes") -> bool:
        return other.is_empty()

    def allows_any(self, other: "VersionTypes") -> bool:
        return False

    def intersect(self, other: "VersionTypes") -> "EmptyConstraint":
        return self

    def union(self, other: "VersionTypes") -> "VersionTypes":
        return other

    def difference(self, other: "VersionTypes") -> "EmptyConstraint":
        return self

    def __str__(self) -> str:
        return "<empty>"
