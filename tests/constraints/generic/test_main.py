from __future__ import annotations

import pytest

from poetry.core.constraints.generic import AnyConstraint
from poetry.core.constraints.generic import Constraint
from poetry.core.constraints.generic import MultiConstraint
from poetry.core.constraints.generic import UnionConstraint
from poetry.core.constraints.generic import parse_constraint
from poetry.core.constraints.generic.constraint import ExtraConstraint
from poetry.core.constraints.generic.multi_constraint import ExtraMultiConstraint
from poetry.core.constraints.generic.parser import parse_extra_constraint


@pytest.mark.parametrize(
    ("input", "constraint"),
    [
        ("*", AnyConstraint()),
        ("win32", Constraint("win32", "=")),
        ("=win32", Constraint("win32", "=")),
        ("==win32", Constraint("win32", "=")),
        ("!=win32", Constraint("win32", "!=")),
        ("!= win32", Constraint("win32", "!=")),
        ("'tegra' not in", Constraint("tegra", "not in")),
        ("'tegra' in", Constraint("tegra", "in")),
    ],
)
def test_parse_constraint(input: str, constraint: AnyConstraint | Constraint) -> None:
    assert parse_constraint(input) == constraint


@pytest.mark.parametrize(
    ("input", "constraint"),
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
        (
            "'tegra' not in,'rpi-v8' not in",
            MultiConstraint(
                Constraint("tegra", "not in"),
                Constraint("rpi-v8", "not in"),
            ),
        ),
    ],
)
def test_parse_constraint_multi(input: str, constraint: MultiConstraint) -> None:
    assert parse_constraint(input) == constraint


@pytest.mark.parametrize(
    ("input", "constraint"),
    [
        ("win32 || linux", UnionConstraint(Constraint("win32"), Constraint("linux"))),
        (
            "win32 || !=linux2",
            UnionConstraint(Constraint("win32"), Constraint("linux2", "!=")),
        ),
        (
            "'tegra' in || 'rpi-v8' in",
            UnionConstraint(Constraint("tegra", "in"), Constraint("rpi-v8", "in")),
        ),
    ],
)
def test_parse_constraint_union(input: str, constraint: UnionConstraint) -> None:
    assert parse_constraint(input) == constraint


def test_constraint_is_not_equal_to_extra_constraint() -> None:
    constraint = Constraint("a", "=")
    extra_constraint = ExtraConstraint("a", "=")
    assert constraint != extra_constraint
    assert extra_constraint != constraint


@pytest.mark.parametrize(
    ("input", "constraint"),
    [
        ("*", AnyConstraint()),
        ("extra1", ExtraConstraint("extra1", "=")),
        ("=extra1", ExtraConstraint("extra1", "=")),
        ("==extra1", ExtraConstraint("extra1", "=")),
        ("!=extra1", ExtraConstraint("extra1", "!=")),
        ("!= extra1", ExtraConstraint("extra1", "!=")),
    ],
)
def test_parse_extra_constraint(
    input: str, constraint: AnyConstraint | Constraint
) -> None:
    parsed_constraint = parse_extra_constraint(input)

    assert type(parsed_constraint) is type(constraint)
    assert parsed_constraint == constraint


@pytest.mark.parametrize(
    ("input", "constraint"),
    [
        (
            "!=extra1,!=extra2",
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
        ),
        (
            "==extra1,==extra2",
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "=="), ExtraConstraint("extra2", "==")
            ),
        ),
        (
            "==extra1,!=extra2,==extra3",
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "=="),
                ExtraConstraint("extra2", "!="),
                ExtraConstraint("extra3", "=="),
            ),
        ),
    ],
)
def test_parse_extra_constraint_multi(input: str, constraint: MultiConstraint) -> None:
    assert parse_extra_constraint(input) == constraint


@pytest.mark.parametrize(
    ("input", "constraint"),
    [
        (
            "extra1 || extra2",
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
        ),
        (
            "extra1 || !=extra2",
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2", "!=")),
        ),
    ],
)
def test_parse_extra_constraint_union(input: str, constraint: UnionConstraint) -> None:
    assert parse_extra_constraint(input) == constraint
