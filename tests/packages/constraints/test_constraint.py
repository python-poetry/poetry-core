from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from poetry.core.packages.constraints import AnyConstraint
from poetry.core.packages.constraints.constraint import Constraint
from poetry.core.packages.constraints.empty_constraint import EmptyConstraint
from poetry.core.packages.constraints.multi_constraint import MultiConstraint
from poetry.core.packages.constraints.union_constraint import UnionConstraint


if TYPE_CHECKING:
    from poetry.core.packages.constraints import BaseConstraint


def test_allows() -> None:
    c = Constraint("win32")

    assert c.allows(Constraint("win32"))
    assert not c.allows(Constraint("linux"))

    c = Constraint("win32", "!=")

    assert not c.allows(Constraint("win32"))
    assert c.allows(Constraint("linux"))


def test_allows_any() -> None:
    c = Constraint("win32")

    assert c.allows_any(Constraint("win32"))
    assert not c.allows_any(Constraint("linux"))
    assert c.allows_any(UnionConstraint(Constraint("win32"), Constraint("linux")))
    assert c.allows_any(Constraint("linux", "!="))

    c = Constraint("win32", "!=")

    assert not c.allows_any(Constraint("win32"))
    assert c.allows_any(Constraint("linux"))
    assert c.allows_any(UnionConstraint(Constraint("win32"), Constraint("linux")))
    assert c.allows_any(Constraint("linux", "!="))


def test_allows_all() -> None:
    c = Constraint("win32")

    assert c.allows_all(Constraint("win32"))
    assert not c.allows_all(Constraint("linux"))
    assert not c.allows_all(Constraint("linux", "!="))
    assert not c.allows_all(UnionConstraint(Constraint("win32"), Constraint("linux")))


@pytest.mark.parametrize(
    ("constraint1", "constraint2", "expected"),
    [
        (
            Constraint("win32"),
            Constraint("win32"),
            Constraint("win32"),
        ),
        (
            Constraint("win32"),
            Constraint("linux"),
            EmptyConstraint(),
        ),
        (
            Constraint("win32"),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            Constraint("win32"),
        ),
        (
            Constraint("win32"),
            UnionConstraint(Constraint("linux"), Constraint("linux2")),
            EmptyConstraint(),
        ),
        (
            Constraint("win32"),
            Constraint("linux", "!="),
            Constraint("win32"),
        ),
        (
            Constraint("win32", "!="),
            Constraint("linux"),
            Constraint("linux"),
        ),
        (
            Constraint("win32", "!="),
            Constraint("linux", "!="),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
        ),
        (
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            UnionConstraint(Constraint("win32"), Constraint("darwin")),
            Constraint("win32"),
        ),
        (
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            MultiConstraint(Constraint("win32", "!="), Constraint("darwin", "!=")),
            Constraint("linux"),
        ),
    ],
)
def test_intersect(
    constraint1: BaseConstraint,
    constraint2: BaseConstraint,
    expected: BaseConstraint,
) -> None:
    intersection = constraint1.intersect(constraint2)
    assert intersection == expected


@pytest.mark.parametrize(
    ("constraint1", "constraint2", "expected"),
    [
        (
            Constraint("win32"),
            Constraint("win32"),
            Constraint("win32"),
        ),
        (
            Constraint("win32"),
            Constraint("linux"),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
        ),
        (
            Constraint("win32"),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
        ),
        (
            Constraint("win32"),
            UnionConstraint(Constraint("linux"), Constraint("linux2")),
            UnionConstraint(
                Constraint("win32"), Constraint("linux"), Constraint("linux2")
            ),
        ),
        (
            Constraint("win32"),
            Constraint("linux", "!="),
            Constraint("linux", "!="),
        ),
        (
            Constraint("win32", "!="),
            Constraint("linux"),
            Constraint("win32", "!="),
        ),
        (
            Constraint("win32", "!="),
            Constraint("linux", "!="),
            AnyConstraint(),
        ),
    ],
)
def test_union(
    constraint1: BaseConstraint,
    constraint2: BaseConstraint,
    expected: BaseConstraint,
) -> None:
    union = constraint1.union(constraint2)
    assert union == expected


def test_difference() -> None:
    c = Constraint("win32")

    assert c.difference(Constraint("win32")).is_empty()
    assert c.difference(Constraint("linux")) == c
