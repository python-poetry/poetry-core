from __future__ import annotations

import operator

from typing import Callable
from typing import ClassVar

from poetry.core.constraints.generic.any_constraint import AnyConstraint
from poetry.core.constraints.generic.base_constraint import BaseConstraint
from poetry.core.constraints.generic.empty_constraint import EmptyConstraint


OperatorType = Callable[[object, object], bool]


def contains(a: object, b: object, /) -> bool:
    return operator.contains(a, b)  # type: ignore[arg-type]


def not_contains(a: object, b: object, /) -> bool:
    return not contains(a, b)


class Constraint(BaseConstraint):
    OP_EQ = operator.eq
    OP_NE = operator.ne
    OP_IN = contains
    OP_NC = not_contains

    _trans_op_str: ClassVar[dict[str, OperatorType]] = {
        "=": OP_EQ,
        "==": OP_EQ,
        "!=": OP_NE,
        "in": OP_IN,
        "not in": OP_NC,
    }

    _trans_op_int: ClassVar[dict[OperatorType, str]] = {
        OP_EQ: "==",
        OP_NE: "!=",
        OP_IN: "in",
        OP_NC: "not in",
    }

    _trans_op_inv: ClassVar[dict[str, str]] = {
        "!=": "==",
        "==": "!=",
        "not in": "in",
        "in": "not in",
    }

    def __init__(self, value: str, operator: str = "==") -> None:
        if operator == "=":
            operator = "=="

        self._value = value
        self._operator = operator
        self._op = self._trans_op_str[operator]

    @property
    def value(self) -> str:
        return self._value

    @property
    def operator(self) -> str:
        return self._operator

    def allows(self, other: BaseConstraint) -> bool:
        if not isinstance(other, Constraint) or other.operator != "==":
            raise ValueError(
                f"Invalid argument for allows"
                f' ("other" must be a constraint with operator "=="): {other}'
            )

        if self._operator == "==":
            return self._value == other.value

        if self._operator == "in":
            return bool(self._trans_op_str["in"](other.value, self._value))

        if self._operator == "!=":
            return self._value != other.value

        if self._operator == "not in":
            return bool(self._trans_op_str["not in"](other.value, self._value))

        return False

    def allows_all(self, other: BaseConstraint) -> bool:
        from poetry.core.constraints.generic import MultiConstraint
        from poetry.core.constraints.generic import UnionConstraint

        if isinstance(other, Constraint):
            is_in_op = self._operator == "in"
            is_not_in_op = self._operator == "not in"

            is_other_equal_op = other.operator == "=="
            is_other_in_op = other.operator == "in"
            is_other_not_in_op = other.operator == "not in"

            if is_other_equal_op:
                return self.allows(other)

            if is_other_in_op and is_in_op:
                return self._op(self.value, other.value)

            if is_other_not_in_op and not is_not_in_op:
                return self._trans_op_str["not in"](other.value, self.value)

            return self == other

        if isinstance(other, MultiConstraint):
            return any(self.allows_all(c) for c in other.constraints)

        if isinstance(other, UnionConstraint):
            return all(self.allows_all(c) for c in other.constraints)

        return other.is_empty()

    def allows_any(self, other: BaseConstraint) -> bool:
        from poetry.core.constraints.generic import MultiConstraint
        from poetry.core.constraints.generic import UnionConstraint

        is_equal_op = self._operator == "=="
        is_non_equal_op = self._operator == "!="
        is_in_op = self._operator == "in"
        is_not_in_op = self._operator == "not in"

        if is_equal_op:
            return other.allows(self)

        if isinstance(other, Constraint):
            is_other_equal_op = other.operator == "=="
            is_other_non_equal_op = other.operator == "!="
            is_other_in_op = other.operator == "in"
            is_other_not_in_op = other.operator == "not in"

            if is_other_equal_op:
                return self.allows(other)

            if is_equal_op and is_other_non_equal_op:
                return self._value != other.value

            return (
                is_in_op
                and is_other_in_op
                or is_not_in_op
                and is_other_not_in_op
                or is_non_equal_op
                and other.operator in {"!=", "in", "not in"}
            )

        elif isinstance(other, MultiConstraint):
            return is_non_equal_op

        elif isinstance(other, UnionConstraint):
            return is_non_equal_op and any(
                self.allows_any(c) for c in other.constraints
            )

        return other.is_any()

    def invert(self) -> Constraint:
        return Constraint(self._value, self._trans_op_inv[self.operator])

    def difference(self, other: BaseConstraint) -> Constraint | EmptyConstraint:
        if other.allows(self):
            return EmptyConstraint()

        return self

    def intersect(self, other: BaseConstraint) -> BaseConstraint:
        from poetry.core.constraints.generic.multi_constraint import MultiConstraint

        if isinstance(other, Constraint):
            if other == self:
                return self

            if self.operator == "!=" and other.operator == "==" and self.allows(other):
                return other

            if other.operator == "!=" and self.operator == "==" and other.allows(self):
                return self

            if (
                other.operator == "!="
                and self.operator == "!="
                or self.operator == "not in"
                and other.operator == "not in"
            ):
                return MultiConstraint(self, other)

            other_in_self = self._trans_op_str["in"](self.value, other.value)
            self_in_other = self._trans_op_str["in"](other.value, self.value)
            is_in_op = self._operator == "in"
            is_other_in_op = other.operator == "in"

            if is_in_op or other.operator == "not in":
                # If self is a subset of other, return self
                if is_other_in_op and other_in_self:
                    return self
                # If neither are subsets of each other then its a MC
                if (is_other_in_op and not self_in_other) or (
                    other.operator == "!=" and self_in_other
                ):
                    return MultiConstraint(self, other)
                # if it allows any of other, return other
                if self.allows_any(other):
                    return other

            if is_other_in_op or self.operator == "not in":
                # If other is a subset of self, return other
                if is_in_op and self_in_other:
                    return other
                # If neither are subsets of each other then its a MC
                if (is_in_op and not other_in_self) or (
                    self.operator == "!=" and other_in_self
                ):
                    return MultiConstraint(self, other)
                # if other allows any of self, return self
                if other.allows_any(self):
                    return self

            return EmptyConstraint()

        return other.intersect(self)

    def union(self, other: BaseConstraint) -> BaseConstraint:
        from poetry.core.constraints.generic.union_constraint import UnionConstraint

        if isinstance(other, Constraint):
            if other == self:
                return self

            if self.operator == "!=" and other.operator == "==" and self.allows(other):
                return self

            if other.operator == "!=" and self.operator == "==" and other.allows(self):
                return other

            if (
                other.operator == "=="
                and self.operator == "=="
                or self.operator == "not in"
                and other.operator == "not in"
            ):
                return UnionConstraint(self, other)

            other_in_self = self._trans_op_str["in"](self.value, other.value)
            self_in_other = self._trans_op_str["in"](other.value, self.value)
            is_in_op = self._operator == "in"
            is_other_in_op = other.operator == "in"

            if is_in_op or other.operator == "not in":
                if is_other_in_op and self_in_other:
                    return self
                if (is_other_in_op and not other_in_self) or (
                    other.operator == "!=" and other_in_self
                ):
                    return UnionConstraint(self, other)
                if other.allows_all(self):
                    return other

            if is_other_in_op or self._operator == "not in":
                if is_in_op and other_in_self:
                    return other
                if (is_in_op and not self_in_other) or (
                    self.operator == "!=" and self_in_other
                ):
                    return UnionConstraint(self, other)
                if self.allows_all(other):
                    return self

            return AnyConstraint()

        # to preserve order (functionally not necessary)
        if isinstance(other, UnionConstraint):
            return UnionConstraint(self).union(other)

        return other.union(self)

    def is_any(self) -> bool:
        return False

    def is_empty(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Constraint):
            return NotImplemented

        return (self.value, self.operator) == (other.value, other.operator)

    def __hash__(self) -> int:
        return hash((self._operator, self._value))

    def __str__(self) -> str:
        space = " " if self._operator in {"in", "not in"} else ""
        op = self._operator if self._operator != "==" else ""
        return f"{op}{space}{self._value}"
