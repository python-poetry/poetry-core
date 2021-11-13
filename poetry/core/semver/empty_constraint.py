from .version_constraint import VersionConstraint


class EmptyConstraint(VersionConstraint):
    def is_empty(self) -> bool:
        return True

    def is_any(self) -> bool:
        return False

    def allows(self, _version: VersionConstraint) -> bool:
        return False

    def allows_all(self, other: VersionConstraint) -> bool:
        return other.is_empty()

    def allows_any(self, _other: VersionConstraint) -> bool:
        return False

    def intersect(self, _other: VersionConstraint) -> "EmptyConstraint":
        return self

    def union(self, other: VersionConstraint) -> VersionConstraint:
        return other

    def difference(self, _other: VersionConstraint) -> "EmptyConstraint":
        return self

    def __str__(self) -> str:
        return "<empty>"
