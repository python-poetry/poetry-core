from __future__ import annotations

import pytest

from poetry.core.constraints.generic import AnyConstraint
from poetry.core.constraints.generic import BaseConstraint
from poetry.core.constraints.generic import Constraint
from poetry.core.constraints.generic import EmptyConstraint
from poetry.core.constraints.generic import MultiConstraint
from poetry.core.constraints.generic import UnionConstraint


def test_allows() -> None:
    c = UnionConstraint(Constraint("win32"), Constraint("linux"))

    assert c.allows(Constraint("win32"))
    assert c.allows(Constraint("linux"))
    assert not c.allows(Constraint("darwin"))


@pytest.mark.parametrize(
    ("constraint", "expected_any", "expected_all"),
    [
        (EmptyConstraint(), False, True),
        (AnyConstraint(), True, False),
        (Constraint("win32"), True, True),
        (Constraint("linux"), True, True),
        (Constraint("darwin"), False, False),
        (Constraint("win32", "!="), True, False),
        (Constraint("linux", "!="), True, False),
        (Constraint("darwin", "!="), True, False),
        (
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            True,
            True,
        ),
        (
            UnionConstraint(
                Constraint("win32"), Constraint("linux"), Constraint("darwin")
            ),
            True,
            False,
        ),
        (
            UnionConstraint(Constraint("darwin"), Constraint("linux")),
            True,
            False,
        ),
        (
            UnionConstraint(Constraint("darwin"), Constraint("osx")),
            False,
            False,
        ),
        (
            UnionConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            True,
            False,
        ),
        (
            UnionConstraint(Constraint("darwin", "!="), Constraint("linux", "!=")),
            True,
            False,
        ),
        (
            UnionConstraint(Constraint("darwin", "!="), Constraint("osx", "!=")),
            True,
            False,
        ),
        (
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            False,
            False,
        ),
        (
            MultiConstraint(
                Constraint("win32", "!="),
                Constraint("linux", "!="),
                Constraint("darwin", "!="),
            ),
            False,
            False,
        ),
        (
            MultiConstraint(Constraint("darwin", "!="), Constraint("linux", "!=")),
            True,
            False,
        ),
        (
            MultiConstraint(Constraint("darwin", "!="), Constraint("osx", "!=")),
            True,
            False,
        ),
    ],
)
def test_allows_any_and_allows_all(
    constraint: BaseConstraint, expected_any: bool, expected_all: bool
) -> None:
    c = UnionConstraint(Constraint("win32"), Constraint("linux"))
    assert c.allows_any(constraint) == expected_any
    assert c.allows_all(constraint) == expected_all
