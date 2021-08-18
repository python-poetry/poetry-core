from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from . import ConstraintTypes  # noqa


class BaseConstraint(object):
    def allows(self, other: "ConstraintTypes") -> bool:
        raise NotImplementedError()

    def allows_all(self, other: "ConstraintTypes") -> bool:
        raise NotImplementedError()

    def allows_any(self, other: "ConstraintTypes") -> bool:
        raise NotImplementedError()

    def difference(self, other: "ConstraintTypes") -> "ConstraintTypes":
        raise NotImplementedError()

    def intersect(self, other: "ConstraintTypes") -> "ConstraintTypes":
        raise NotImplementedError()

    def union(self, other: "ConstraintTypes") -> "ConstraintTypes":
        raise NotImplementedError()

    def is_any(self) -> bool:
        return False

    def is_empty(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "<{} {}>".format(self.__class__.__name__, str(self))

    def __eq__(self, other: "ConstraintTypes") -> bool:
        raise NotImplementedError()
