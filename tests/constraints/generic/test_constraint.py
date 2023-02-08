from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from poetry.core.constraints.generic import AnyConstraint
from poetry.core.constraints.generic import Constraint
from poetry.core.constraints.generic import EmptyConstraint
from poetry.core.constraints.generic import MultiConstraint
from poetry.core.constraints.generic import UnionConstraint


if TYPE_CHECKING:
    from poetry.core.constraints.generic import BaseConstraint


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
            EmptyConstraint(),
            Constraint("win32"),
            EmptyConstraint(),
        ),
        (
            EmptyConstraint(),
            MultiConstraint(Constraint("darwin", "!="), Constraint("linux", "!=")),
            EmptyConstraint(),
        ),
        (
            EmptyConstraint(),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            EmptyConstraint(),
        ),
        (
            AnyConstraint(),
            Constraint("win32"),
            Constraint("win32"),
        ),
        (
            AnyConstraint(),
            MultiConstraint(Constraint("darwin", "!="), Constraint("linux", "!=")),
            MultiConstraint(Constraint("darwin", "!="), Constraint("linux", "!=")),
        ),
        (
            AnyConstraint(),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
        ),
        (
            EmptyConstraint(),
            AnyConstraint(),
            EmptyConstraint(),
        ),
        (
            EmptyConstraint(),
            EmptyConstraint(),
            EmptyConstraint(),
        ),
        (
            AnyConstraint(),
            AnyConstraint(),
            AnyConstraint(),
        ),
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
            MultiConstraint(Constraint("darwin", "!="), Constraint("linux", "!=")),
            Constraint("win32"),
        ),
        (
            Constraint("win32"),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
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
            Constraint("win32", "!="),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
        ),
        (
            Constraint("darwin", "!="),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            MultiConstraint(
                Constraint("win32", "!="),
                Constraint("linux", "!="),
                Constraint("darwin", "!="),
            ),
        ),
        (
            Constraint("win32", "!="),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            Constraint("linux"),
        ),
        (
            Constraint("win32", "!="),
            UnionConstraint(
                Constraint("win32"), Constraint("linux"), Constraint("darwin")
            ),
            UnionConstraint(Constraint("linux"), Constraint("darwin")),
        ),
        (
            Constraint("win32", "!="),
            UnionConstraint(Constraint("linux"), Constraint("linux2")),
            UnionConstraint(Constraint("linux"), Constraint("linux2")),
        ),
        (
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            UnionConstraint(Constraint("win32"), Constraint("darwin")),
            Constraint("win32"),
        ),
        (
            UnionConstraint(
                Constraint("win32"), Constraint("linux"), Constraint("darwin")
            ),
            UnionConstraint(
                Constraint("win32"), Constraint("cygwin"), Constraint("darwin")
            ),
            UnionConstraint(
                Constraint("win32"),
                Constraint("darwin"),
            ),
        ),
        (
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            MultiConstraint(Constraint("win32", "!="), Constraint("darwin", "!=")),
            Constraint("linux"),
        ),
        (
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            EmptyConstraint(),
        ),
    ],
)
def test_intersect(
    constraint1: BaseConstraint,
    constraint2: BaseConstraint,
    expected: BaseConstraint,
) -> None:
    assert constraint1.intersect(constraint2) == expected
    assert constraint2.intersect(constraint1) == expected


@pytest.mark.parametrize(
    ("constraint1", "constraint2", "expected"),
    [
        (
            EmptyConstraint(),
            Constraint("win32"),
            Constraint("win32"),
        ),
        (
            EmptyConstraint(),
            MultiConstraint(Constraint("darwin", "!="), Constraint("linux", "!=")),
            MultiConstraint(Constraint("darwin", "!="), Constraint("linux", "!=")),
        ),
        (
            EmptyConstraint(),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
        ),
        (
            AnyConstraint(),
            Constraint("win32"),
            AnyConstraint(),
        ),
        (
            AnyConstraint(),
            MultiConstraint(Constraint("darwin", "!="), Constraint("linux", "!=")),
            AnyConstraint(),
        ),
        (
            AnyConstraint(),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            AnyConstraint(),
        ),
        (
            EmptyConstraint(),
            AnyConstraint(),
            AnyConstraint(),
        ),
        (
            EmptyConstraint(),
            EmptyConstraint(),
            EmptyConstraint(),
        ),
        (
            AnyConstraint(),
            AnyConstraint(),
            AnyConstraint(),
        ),
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
            MultiConstraint(Constraint("darwin", "!="), Constraint("linux", "!=")),
            MultiConstraint(Constraint("darwin", "!="), Constraint("linux", "!=")),
        ),
        (
            Constraint("win32"),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            Constraint("linux", "!="),
        ),
        (
            Constraint("win32"),
            MultiConstraint(
                Constraint("win32", "!="),
                Constraint("linux", "!="),
                Constraint("darwin", "!="),
            ),
            MultiConstraint(Constraint("linux", "!="), Constraint("darwin", "!=")),
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
        (
            Constraint("win32", "!="),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            Constraint("win32", "!="),
        ),
        (
            Constraint("darwin", "!="),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            AnyConstraint(),
        ),
        (
            Constraint("win32", "!="),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            AnyConstraint(),
        ),
        (
            Constraint("win32", "!="),
            UnionConstraint(Constraint("linux"), Constraint("linux2")),
            Constraint("win32", "!="),
        ),
        (
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            UnionConstraint(Constraint("win32"), Constraint("darwin")),
            UnionConstraint(
                Constraint("win32"), Constraint("linux"), Constraint("darwin")
            ),
        ),
        (
            UnionConstraint(
                Constraint("win32"), Constraint("linux"), Constraint("darwin")
            ),
            UnionConstraint(
                Constraint("win32"), Constraint("cygwin"), Constraint("darwin")
            ),
            UnionConstraint(
                Constraint("win32"),
                Constraint("linux"),
                Constraint("darwin"),
                Constraint("cygwin"),
            ),
        ),
        (
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            MultiConstraint(Constraint("win32", "!="), Constraint("darwin", "!=")),
            UnionConstraint(
                Constraint("win32"),
                Constraint("linux"),
                MultiConstraint(Constraint("win32", "!="), Constraint("darwin", "!=")),
            ),
        ),
        (
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            UnionConstraint(
                Constraint("win32"),
                Constraint("linux"),
                MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            ),
        ),
    ],
)
def test_union(
    constraint1: BaseConstraint,
    constraint2: BaseConstraint,
    expected: BaseConstraint,
) -> None:
    assert constraint1.union(constraint2) == expected
    assert constraint2.union(constraint1) == expected


def test_difference() -> None:
    c = Constraint("win32")

    assert c.difference(Constraint("win32")).is_empty()
    assert c.difference(Constraint("linux")) == c


@pytest.mark.parametrize(
    "constraint",
    [
        EmptyConstraint(),
        AnyConstraint(),
        Constraint("win32"),
        UnionConstraint(Constraint("win32"), Constraint("linux")),
        MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
    ],
)
def test_constraints_are_hashable(constraint: BaseConstraint) -> None:
    # We're just testing that constraints are hashable, there's nothing much to say
    # about the result.
    hash(constraint)
