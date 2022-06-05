from __future__ import annotations

from poetry.core.packages.constraints.base_constraint import BaseConstraint


class EmptyConstraint(BaseConstraint):
    pretty_string = None

    def matches(self, _: BaseConstraint) -> bool:
        return True

    def is_empty(self) -> bool:
        return True

    def allows(self, other: BaseConstraint) -> bool:
        return False

    def allows_all(self, other: BaseConstraint) -> bool:
        return other.is_empty()

    def allows_any(self, other: BaseConstraint) -> bool:
        return False

    def intersect(self, other: BaseConstraint) -> BaseConstraint:
        return self

    def difference(self, other: BaseConstraint) -> BaseConstraint:
        return self

    def __eq__(self, other: object) -> bool:
        return other.is_empty() if isinstance(other, BaseConstraint) else False

    def __str__(self) -> str:
        return ""
