from typing import TYPE_CHECKING

from .base_constraint import BaseConstraint


if TYPE_CHECKING:
    from . import ConstraintTypes  # noqa


class EmptyConstraint(BaseConstraint):

    pretty_string = None

    def matches(self, _: "ConstraintTypes") -> bool:
        return True

    def is_empty(self) -> bool:
        return True

    def allows(self, other: "ConstraintTypes") -> bool:
        return False

    def allows_all(self, other: "ConstraintTypes") -> bool:
        return True

    def allows_any(self, other: "ConstraintTypes") -> bool:
        return True

    def intersect(self, other: "ConstraintTypes") -> "ConstraintTypes":
        return other

    def difference(self, other: "ConstraintTypes") -> None:
        return

    def __eq__(self, other: "ConstraintTypes") -> bool:
        return other.is_empty()

    def __str__(self) -> str:
        return ""
