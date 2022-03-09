from __future__ import annotations

from typing import TYPE_CHECKING

from poetry.core.semver.version_constraint import VersionConstraint


if TYPE_CHECKING:
    from poetry.core.semver.version import Version


class EmptyConstraint(VersionConstraint):
    def is_empty(self) -> bool:
        return True

    def is_any(self) -> bool:
        return False

    def is_simple(self) -> bool:
        return True

    def allows(self, version: Version) -> bool:
        return False

    def allows_all(self, other: VersionConstraint) -> bool:
        return other.is_empty()

    def allows_any(self, other: VersionConstraint) -> bool:
        return False

    def intersect(self, other: VersionConstraint) -> EmptyConstraint:
        return self

    def union(self, other: VersionConstraint) -> VersionConstraint:
        return other

    def difference(self, other: VersionConstraint) -> EmptyConstraint:
        return self

    def __str__(self) -> str:
        return "<empty>"
