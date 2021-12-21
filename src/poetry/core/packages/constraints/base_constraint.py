from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from poetry.core.packages.constraints import ConstraintTypes  # noqa


class BaseConstraint:
    def allows(self, _other: "ConstraintTypes") -> bool:
        raise NotImplementedError()

    def allows_all(self, _other: "ConstraintTypes") -> bool:
        raise NotImplementedError()

    def allows_any(self, _other: "ConstraintTypes") -> bool:
        raise NotImplementedError()

    def difference(self, _other: "ConstraintTypes") -> "ConstraintTypes":
        raise NotImplementedError()

    def intersect(self, _other: "ConstraintTypes") -> "ConstraintTypes":
        raise NotImplementedError()

    def union(self, _other: "ConstraintTypes") -> "ConstraintTypes":
        raise NotImplementedError()

    def is_any(self) -> bool:
        return False

    def is_empty(self) -> bool:
        return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {str(self)}>"

    def __eq__(self, _other: object) -> bool:
        return NotImplemented
