from typing import TYPE_CHECKING

from .base_constraint import BaseConstraint
from .empty_constraint import EmptyConstraint


if TYPE_CHECKING:
    from . import ConstraintTypes  # noqa


class AnyConstraint(BaseConstraint):
    def allows(self, other: "ConstraintTypes") -> bool:
        return True

    def allows_all(self, other: "ConstraintTypes") -> bool:
        return True

    def allows_any(self, other: "ConstraintTypes") -> bool:
        return True

    def difference(self, other: "ConstraintTypes") -> "ConstraintTypes":
        if other.is_any():
            return EmptyConstraint()

        return other

    def intersect(self, other: "ConstraintTypes") -> "ConstraintTypes":
        return other

    def union(self, other: "ConstraintTypes") -> "AnyConstraint":
        return AnyConstraint()

    def is_any(self) -> bool:
        return True

    def is_empty(self) -> bool:
        return False

    def __str__(self) -> str:
        return "*"

    def __eq__(self, other: "ConstraintTypes") -> bool:
        return other.is_any()
