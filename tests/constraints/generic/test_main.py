from __future__ import annotations

import pytest

from poetry.core.constraints.generic import AnyConstraint
from poetry.core.constraints.generic import Constraint
from poetry.core.constraints.generic import MultiConstraint
from poetry.core.constraints.generic import UnionConstraint
from poetry.core.constraints.generic import parse_constraint


@pytest.mark.parametrize(
    "input,constraint",
    [
        ("*", AnyConstraint()),
        ("win32", Constraint("win32", "=")),
        ("=win32", Constraint("win32", "=")),
        ("==win32", Constraint("win32", "=")),
        ("!=win32", Constraint("win32", "!=")),
        ("!= win32", Constraint("win32", "!=")),
    ],
)
def test_parse_constraint(input: str, constraint: AnyConstraint | Constraint) -> None:
    assert parse_constraint(input) == constraint


@pytest.mark.parametrize(
    "input,constraint",
    [
        (
            "!=win32,!=linux",
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
        ),
        (
            "!=win32,!=linux,!=linux2",
            MultiConstraint(
                Constraint("win32", "!="),
                Constraint("linux", "!="),
                Constraint("linux2", "!="),
            ),
        ),
    ],
)
def test_parse_constraint_multi(input: str, constraint: MultiConstraint) -> None:
    assert parse_constraint(input) == constraint


@pytest.mark.parametrize(
    "input,constraint",
    [
        ("win32 || linux", UnionConstraint(Constraint("win32"), Constraint("linux"))),
        (
            "win32 || !=linux2",
            UnionConstraint(Constraint("win32"), Constraint("linux2", "!=")),
        ),
    ],
)
def test_parse_constraint_union(input: str, constraint: UnionConstraint) -> None:
    assert parse_constraint(input) == constraint
