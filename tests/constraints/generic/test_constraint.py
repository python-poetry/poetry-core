from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from poetry.core.constraints.generic import AnyConstraint
from poetry.core.constraints.generic import Constraint
from poetry.core.constraints.generic import EmptyConstraint
from poetry.core.constraints.generic import MultiConstraint
from poetry.core.constraints.generic import UnionConstraint
from poetry.core.constraints.generic.constraint import ExtraConstraint
from poetry.core.constraints.generic.multi_constraint import ExtraMultiConstraint


if TYPE_CHECKING:
    from poetry.core.constraints.generic import BaseConstraint


@pytest.mark.parametrize(
    ("constraint1", "constraint2", "expected"),
    [
        (Constraint("win32"), Constraint("win32"), True),
        (Constraint("win32"), Constraint("linux"), False),
        (Constraint("win32", "!="), Constraint("win32"), False),
        (Constraint("win32", "!="), Constraint("linux"), True),
        (Constraint("tegra", "in"), Constraint("1.2-tegra"), True),
        (Constraint("tegra", "in"), Constraint("1.2-teg"), False),
        (Constraint("tegra", "not in"), Constraint("1.2-tegra"), False),
        (Constraint("tegra", "not in"), Constraint("1.2-teg"), True),
    ],
)
def test_allows(
    constraint1: Constraint, constraint2: Constraint, expected: bool
) -> None:
    assert constraint1.allows(constraint2) is expected
    # allows_any() and allows_all() should be the same as allows()
    # if the second constraint is a `==` constraint
    assert constraint1.allows_any(constraint2) is expected
    assert constraint1.allows_all(constraint2) is expected


@pytest.mark.parametrize(
    ("constraint1", "constraint2", "expected_any", "expected_all"),
    [
        (Constraint("win32"), EmptyConstraint(), False, True),
        (Constraint("win32"), AnyConstraint(), True, False),
        (Constraint("win32"), Constraint("win32"), True, True),
        (Constraint("win32"), Constraint("linux"), False, False),
        (Constraint("win32"), Constraint("win32", "!="), False, False),
        (Constraint("win32"), Constraint("linux", "!="), True, False),
        (
            Constraint("win32"),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            True,
            False,
        ),
        (
            Constraint("win32"),
            UnionConstraint(Constraint("darwin"), Constraint("linux")),
            False,
            False,
        ),
        (
            Constraint("win32"),
            UnionConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            True,
            False,
        ),
        (
            Constraint("win32"),
            UnionConstraint(Constraint("darwin", "!="), Constraint("linux", "!=")),
            True,
            False,
        ),
        (
            Constraint("win32"),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            False,
            False,
        ),
        (
            Constraint("win32"),
            MultiConstraint(Constraint("darwin", "!="), Constraint("linux", "!=")),
            True,
            False,
        ),
        (Constraint("win32", "!="), EmptyConstraint(), False, True),
        (Constraint("win32", "!="), AnyConstraint(), True, False),
        (Constraint("win32", "!="), Constraint("win32"), False, False),
        (Constraint("win32", "!="), Constraint("linux"), True, True),
        (Constraint("win32", "!="), Constraint("win32", "!="), True, True),
        (Constraint("win32", "!="), Constraint("linux", "!="), True, False),
        (
            Constraint("win32", "!="),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            True,
            False,
        ),
        (
            Constraint("win32", "!="),
            UnionConstraint(Constraint("darwin"), Constraint("linux")),
            True,
            True,
        ),
        (
            Constraint("win32", "!="),
            UnionConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            True,
            False,
        ),
        (
            Constraint("win32", "!="),
            UnionConstraint(Constraint("darwin", "!="), Constraint("linux", "!=")),
            True,
            False,
        ),
        (
            Constraint("win32", "!="),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            True,
            True,
        ),
        (
            Constraint("win32", "!="),
            MultiConstraint(Constraint("darwin", "!="), Constraint("linux", "!=")),
            True,
            False,
        ),
        (
            Constraint("tegra", "not in"),
            Constraint("tegra", "not in"),
            True,
            True,
        ),
        (
            Constraint("tegra", "in"),
            Constraint("tegra", "not in"),
            False,
            False,
        ),
        (
            Constraint("tegra", "in"),
            Constraint("tegra", "in"),
            True,
            True,
        ),
        (
            Constraint("tegra", "not in"),
            Constraint("tegra", "in"),
            False,
            False,
        ),
        (
            Constraint("tegra", "in"),
            Constraint("teg", "in"),
            True,
            False,
        ),
        (
            Constraint("teg", "in"),
            Constraint("tegra", "in"),
            True,
            True,
        ),
        (
            Constraint("teg", "not in"),
            Constraint("tegra", "not in"),
            True,
            False,
        ),
        (
            Constraint("tegra", "not in"),
            Constraint("teg", "not in"),
            True,
            True,
        ),
        (
            Constraint("teg", "not in"),
            Constraint("tegra", "in"),
            False,
            False,
        ),
        (
            Constraint("tegra", "in"),
            Constraint("teg", "not in"),
            False,
            False,
        ),
        (
            Constraint("teg", "in"),
            Constraint("tegra", "not in"),
            True,
            False,
        ),
        (
            Constraint("tegra", "not in"),
            Constraint("teg", "in"),
            True,
            False,
        ),
        (
            Constraint("tegra", "in"),
            Constraint("rpi", "in"),
            True,
            False,
        ),
        (
            Constraint("1.2.3-tegra", "!="),
            Constraint("tegra", "in"),
            True,
            False,
        ),
        (
            Constraint("tegra", "in"),
            Constraint("1.2.3-tegra", "!="),
            True,
            False,
        ),
        (
            Constraint("1.2.3-tegra", "!="),
            Constraint("teg", "in"),
            True,
            False,
        ),
        (
            Constraint("teg", "in"),
            Constraint("1.2.3-tegra", "!="),
            True,
            False,
        ),
        (
            Constraint("1.2.3-tegra", "!="),
            Constraint("tegra", "not in"),
            True,
            True,
        ),
        (
            Constraint("tegra", "not in"),
            Constraint("1.2.3-tegra", "!="),
            True,
            False,
        ),
        (
            Constraint("1.2.3-tegra", "!="),
            Constraint("teg", "not in"),
            True,
            True,
        ),
        (
            Constraint("teg", "not in"),
            Constraint("1.2.3-tegra", "!="),
            True,
            False,
        ),
        (
            Constraint("1.2.3-tegra", "=="),
            Constraint("tegra", "in"),
            True,
            False,
        ),
        (
            Constraint("1.2.3-tegra", "=="),
            Constraint("tegra", "not in"),
            False,
            False,
        ),
    ],
)
def test_allows_any_and_allows_all(
    constraint1: Constraint,
    constraint2: BaseConstraint,
    expected_any: bool,
    expected_all: bool,
) -> None:
    assert constraint1.allows_any(constraint2) is expected_any
    assert constraint1.allows_all(constraint2) is expected_all


@pytest.mark.parametrize(
    ("constraint", "inverted"),
    [
        (EmptyConstraint(), AnyConstraint()),
        (Constraint("foo"), Constraint("foo", "!=")),
        (
            MultiConstraint(Constraint("foo", "!="), Constraint("bar", "!=")),
            UnionConstraint(Constraint("foo"), Constraint("bar")),
        ),
        (Constraint("tegra", "not in"), Constraint("tegra", "in")),
    ],
)
def test_invert(constraint: BaseConstraint, inverted: BaseConstraint) -> None:
    assert constraint.invert() == inverted
    assert inverted.invert() == constraint


@pytest.mark.parametrize(
    ("constraint", "inverted"),
    [
        (ExtraConstraint("foo"), ExtraConstraint("foo", "!=")),
        (
            ExtraMultiConstraint(ExtraConstraint("foo"), ExtraConstraint("bar", "!=")),
            UnionConstraint(ExtraConstraint("foo", "!="), ExtraConstraint("bar")),
        ),
    ],
)
def test_invert_extra(constraint: BaseConstraint, inverted: BaseConstraint) -> None:
    assert constraint.invert() == inverted
    assert inverted.invert() == constraint


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
            (
                MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
                MultiConstraint(Constraint("linux", "!="), Constraint("win32", "!=")),
            ),
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
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
        ),
        (
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            UnionConstraint(Constraint("linux"), Constraint("win32")),
            (
                UnionConstraint(Constraint("win32"), Constraint("linux")),
                UnionConstraint(Constraint("linux"), Constraint("win32")),
            ),
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
        (
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
        ),
        (
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            MultiConstraint(Constraint("linux", "!="), Constraint("win32", "!=")),
            (
                MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
                MultiConstraint(Constraint("linux", "!="), Constraint("win32", "!=")),
            ),
        ),
        (
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            MultiConstraint(Constraint("win32", "!="), Constraint("darwin", "!=")),
            (
                MultiConstraint(
                    Constraint("win32", "!="),
                    Constraint("linux", "!="),
                    Constraint("darwin", "!="),
                ),
                MultiConstraint(
                    Constraint("win32", "!="),
                    Constraint("darwin", "!="),
                    Constraint("linux", "!="),
                ),
            ),
        ),
        (
            Constraint("tegra", "not in"),
            Constraint("tegra", "not in"),
            Constraint("tegra", "not in"),
        ),
        (
            Constraint("tegra", "in"),
            Constraint("tegra", "not in"),
            EmptyConstraint(),
        ),
        (
            Constraint("tegra", "in"),
            Constraint("tegra", "in"),
            Constraint("tegra", "in"),
        ),
        (
            Constraint("teg", "in"),
            Constraint("tegra", "in"),
            Constraint("tegra", "in"),
        ),
        (
            Constraint("teg", "not in"),
            Constraint("tegra", "in"),
            EmptyConstraint(),
        ),
        (
            Constraint("teg", "in"),
            Constraint("tegra", "not in"),
            (
                MultiConstraint(Constraint("teg", "in"), Constraint("tegra", "not in")),
                MultiConstraint(Constraint("tegra", "not in"), Constraint("teg", "in")),
            ),
        ),
        (
            Constraint("tegra", "in"),
            Constraint("rpi", "in"),
            (
                MultiConstraint(Constraint("tegra", "in"), Constraint("rpi", "in")),
                MultiConstraint(Constraint("rpi", "in"), Constraint("tegra", "in")),
            ),
        ),
        (
            Constraint("tegra", "in"),
            Constraint("1.2.3-tegra", "=="),
            Constraint("1.2.3-tegra", "=="),
        ),
        (
            Constraint("tegra", "in"),
            Constraint("1.2.3-tegra", "!="),
            (
                MultiConstraint(
                    Constraint("tegra", "in"), Constraint("1.2.3-tegra", "!=")
                ),
                MultiConstraint(
                    Constraint("1.2.3-tegra", "!="),
                    Constraint("tegra", "in"),
                ),
            ),
        ),
        (
            Constraint("tegra", "not in"),
            Constraint("1.2.3-tegra", "=="),
            EmptyConstraint(),
        ),
        (
            Constraint("tegra", "not in"),
            Constraint("1.2.3-tegra", "!="),
            Constraint("tegra", "not in"),
        ),
        (
            Constraint("tegra", "not in"),
            Constraint("rpi", "not in"),
            (
                MultiConstraint(
                    Constraint("tegra", "not in"),
                    Constraint("rpi", "not in"),
                ),
                MultiConstraint(
                    Constraint("rpi", "not in"),
                    Constraint("tegra", "not in"),
                ),
            ),
        ),
    ],
)
def test_intersect(
    constraint1: BaseConstraint,
    constraint2: BaseConstraint,
    expected: BaseConstraint | tuple[BaseConstraint, BaseConstraint],
) -> None:
    if not isinstance(expected, tuple):
        expected = (expected, expected)
    assert constraint1.intersect(constraint2) == expected[0]
    assert constraint2.intersect(constraint1) == expected[1]


@pytest.mark.parametrize(
    ("constraint1", "constraint2", "expected"),
    [
        (
            EmptyConstraint(),
            ExtraConstraint("extra1"),
            EmptyConstraint(),
        ),
        (
            EmptyConstraint(),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
            EmptyConstraint(),
        ),
        (
            EmptyConstraint(),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            EmptyConstraint(),
        ),
        (
            AnyConstraint(),
            ExtraConstraint("extra1"),
            ExtraConstraint("extra1"),
        ),
        (
            AnyConstraint(),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
        ),
        (
            AnyConstraint(),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
        ),
        (
            ExtraConstraint("extra1"),
            ExtraConstraint("extra1"),
            ExtraConstraint("extra1"),
        ),
        (
            ExtraConstraint("extra1"),
            ExtraConstraint("extra1", "!="),
            EmptyConstraint(),
        ),
        (
            ExtraConstraint("extra1"),
            ExtraConstraint("extra2"),
            (
                ExtraMultiConstraint(
                    ExtraConstraint("extra1"), ExtraConstraint("extra2")
                ),
                ExtraMultiConstraint(
                    ExtraConstraint("extra2"), ExtraConstraint("extra1")
                ),
            ),
        ),
        (
            ExtraConstraint("extra1"),
            ExtraMultiConstraint(
                ExtraConstraint("extra2", "!="), ExtraConstraint("extra3", "!=")
            ),
            ExtraMultiConstraint(
                ExtraConstraint("extra2", "!="),
                ExtraConstraint("extra3", "!="),
                ExtraConstraint("extra1"),
            ),
        ),
        (
            ExtraConstraint("extra1"),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
            EmptyConstraint(),
        ),
        (
            ExtraConstraint("extra1"),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraConstraint("extra1"),
        ),
        (
            ExtraConstraint("extra1"),
            UnionConstraint(ExtraConstraint("extra2"), ExtraConstraint("extra3")),
            UnionConstraint(
                ExtraMultiConstraint(
                    ExtraConstraint("extra2"), ExtraConstraint("extra1")
                ),
                ExtraMultiConstraint(
                    ExtraConstraint("extra3"), ExtraConstraint("extra1")
                ),
            ),
        ),
        (
            ExtraConstraint("extra1"),
            ExtraConstraint("extra2", "!="),
            (
                ExtraMultiConstraint(
                    ExtraConstraint("extra1"), ExtraConstraint("extra2", "!=")
                ),
                ExtraMultiConstraint(
                    ExtraConstraint("extra2", "!="), ExtraConstraint("extra1")
                ),
            ),
        ),
        (
            ExtraConstraint("extra1", "!="),
            ExtraConstraint("extra2"),
            (
                ExtraMultiConstraint(
                    ExtraConstraint("extra1", "!="), ExtraConstraint("extra2")
                ),
                ExtraMultiConstraint(
                    ExtraConstraint("extra2"), ExtraConstraint("extra1", "!=")
                ),
            ),
        ),
        (
            ExtraConstraint("extra1", "!="),
            ExtraConstraint("extra2", "!="),
            (
                ExtraMultiConstraint(
                    ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
                ),
                ExtraMultiConstraint(
                    ExtraConstraint("extra2", "!="), ExtraConstraint("extra1", "!=")
                ),
            ),
        ),
        (
            ExtraConstraint("extra1", "!="),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
        ),
        (
            ExtraConstraint("extra3", "!="),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="),
                ExtraConstraint("extra2", "!="),
                ExtraConstraint("extra3", "!="),
            ),
        ),
        (
            ExtraConstraint("extra1", "!="),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(
                ExtraConstraint("extra2"), ExtraConstraint("extra1", "!=")
            ),
        ),
        (
            ExtraConstraint("extra1", "!="),
            UnionConstraint(
                ExtraConstraint("extra1"),
                ExtraConstraint("extra2"),
                ExtraConstraint("extra3"),
            ),
            UnionConstraint(
                ExtraMultiConstraint(
                    ExtraConstraint("extra2"), ExtraConstraint("extra1", "!=")
                ),
                ExtraMultiConstraint(
                    ExtraConstraint("extra3"), ExtraConstraint("extra1", "!=")
                ),
            ),
        ),
        (
            ExtraConstraint("extra1", "!="),
            UnionConstraint(ExtraConstraint("extra2"), ExtraConstraint("extra3")),
            UnionConstraint(
                ExtraMultiConstraint(
                    ExtraConstraint("extra2"), ExtraConstraint("extra1", "!=")
                ),
                ExtraMultiConstraint(
                    ExtraConstraint("extra3"), ExtraConstraint("extra1", "!=")
                ),
            ),
        ),
        (
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
        ),
        (
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(ExtraConstraint("extra2"), ExtraConstraint("extra1")),
            (
                ExtraMultiConstraint(
                    ExtraConstraint("extra1"), ExtraConstraint("extra2")
                ),
                ExtraMultiConstraint(
                    ExtraConstraint("extra2"), ExtraConstraint("extra1")
                ),
            ),
        ),
        (
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
        ),
        (
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            UnionConstraint(
                ExtraConstraint("extra1"),
                ExtraConstraint("extra2"),
                ExtraConstraint("extra3"),
            ),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
        ),
        (
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            UnionConstraint(ExtraConstraint("extra2"), ExtraConstraint("extra1")),
            (
                UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
                UnionConstraint(ExtraConstraint("extra2"), ExtraConstraint("extra1")),
            ),
        ),
        (
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra3")),
            (
                UnionConstraint(
                    ExtraConstraint("extra1"),
                    ExtraMultiConstraint(
                        ExtraConstraint("extra1"), ExtraConstraint("extra3")
                    ),
                    ExtraMultiConstraint(
                        ExtraConstraint("extra2"), ExtraConstraint("extra1")
                    ),
                    ExtraMultiConstraint(
                        ExtraConstraint("extra2"), ExtraConstraint("extra3")
                    ),
                ),
                UnionConstraint(
                    ExtraConstraint("extra1"),
                    ExtraMultiConstraint(
                        ExtraConstraint("extra1"), ExtraConstraint("extra2")
                    ),
                    ExtraMultiConstraint(
                        ExtraConstraint("extra3"), ExtraConstraint("extra1")
                    ),
                    ExtraMultiConstraint(
                        ExtraConstraint("extra3"), ExtraConstraint("extra2")
                    ),
                ),
            ),
        ),
        (
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra3", "!=")
            ),
            ExtraMultiConstraint(
                ExtraConstraint("extra2"),
                ExtraConstraint("extra1", "!="),
                ExtraConstraint("extra3", "!="),
            ),
        ),
        (
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
            EmptyConstraint(),
        ),
        (
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra3", "!=")
            ),
            (
                ExtraMultiConstraint(
                    ExtraConstraint("extra1", "!="),
                    ExtraConstraint("extra2", "!="),
                    ExtraConstraint("extra3", "!="),
                ),
                ExtraMultiConstraint(
                    ExtraConstraint("extra1", "!="),
                    ExtraConstraint("extra3", "!="),
                    ExtraConstraint("extra2", "!="),
                ),
            ),
        ),
        (
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra3", "!=")
            ),
            EmptyConstraint(),
        ),
        (
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(
                ExtraConstraint("extra3", "!="), ExtraConstraint("extra4", "!=")
            ),
            (
                ExtraMultiConstraint(
                    ExtraConstraint("extra1"),
                    ExtraConstraint("extra2"),
                    ExtraConstraint("extra3", "!="),
                    ExtraConstraint("extra4", "!="),
                ),
                ExtraMultiConstraint(
                    ExtraConstraint("extra3", "!="),
                    ExtraConstraint("extra4", "!="),
                    ExtraConstraint("extra1"),
                    ExtraConstraint("extra2"),
                ),
            ),
        ),
        (
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            EmptyConstraint(),
        ),
        (
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
        ),
    ],
)
def test_intersect_extra(
    constraint1: BaseConstraint,
    constraint2: BaseConstraint,
    expected: BaseConstraint | tuple[BaseConstraint, BaseConstraint],
) -> None:
    if not isinstance(expected, tuple):
        expected = (expected, expected)
    assert constraint1.intersect(constraint2) == expected[0]
    assert constraint2.intersect(constraint1) == expected[1]


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
            (
                UnionConstraint(Constraint("win32"), Constraint("linux")),
                UnionConstraint(Constraint("linux"), Constraint("win32")),
            ),
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
            (
                UnionConstraint(
                    Constraint("win32"), Constraint("linux"), Constraint("linux2")
                ),
                UnionConstraint(
                    Constraint("linux"), Constraint("linux2"), Constraint("win32")
                ),
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
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            UnionConstraint(Constraint("win32"), Constraint("linux")),
        ),
        (
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            UnionConstraint(Constraint("linux"), Constraint("win32")),
            (
                UnionConstraint(Constraint("win32"), Constraint("linux")),
                UnionConstraint(Constraint("linux"), Constraint("win32")),
            ),
        ),
        (
            UnionConstraint(Constraint("win32"), Constraint("linux")),
            UnionConstraint(Constraint("win32"), Constraint("darwin")),
            (
                UnionConstraint(
                    Constraint("win32"), Constraint("linux"), Constraint("darwin")
                ),
                UnionConstraint(
                    Constraint("win32"), Constraint("darwin"), Constraint("linux")
                ),
            ),
        ),
        (
            UnionConstraint(
                Constraint("win32"), Constraint("linux"), Constraint("darwin")
            ),
            UnionConstraint(
                Constraint("win32"), Constraint("cygwin"), Constraint("darwin")
            ),
            (
                UnionConstraint(
                    Constraint("win32"),
                    Constraint("linux"),
                    Constraint("darwin"),
                    Constraint("cygwin"),
                ),
                UnionConstraint(
                    Constraint("win32"),
                    Constraint("cygwin"),
                    Constraint("darwin"),
                    Constraint("linux"),
                ),
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
        (
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
        ),
        (
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            MultiConstraint(Constraint("linux", "!="), Constraint("win32", "!=")),
            (
                MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
                MultiConstraint(Constraint("linux", "!="), Constraint("win32", "!=")),
            ),
        ),
        (
            MultiConstraint(Constraint("win32", "!="), Constraint("linux", "!=")),
            MultiConstraint(Constraint("win32", "!="), Constraint("darwin", "!=")),
            MultiConstraint(Constraint("win32", "!=")),
        ),
        (
            Constraint("tegra", "not in"),
            Constraint("tegra", "not in"),
            Constraint("tegra", "not in"),
        ),
        (
            Constraint("tegra", "in"),
            Constraint("tegra", "not in"),
            AnyConstraint(),
        ),
        (
            Constraint("tegra", "in"),
            Constraint("tegra", "in"),
            Constraint("tegra", "in"),
        ),
        (
            Constraint("teg", "in"),
            Constraint("tegra", "in"),
            Constraint("teg", "in"),
        ),
        (
            Constraint("teg", "in"),
            Constraint("tegra", "not in"),
            AnyConstraint(),
        ),
        (
            Constraint("teg", "not in"),
            Constraint("tegra", "in"),
            (
                UnionConstraint(Constraint("teg", "not in"), Constraint("tegra", "in")),
                UnionConstraint(Constraint("tegra", "in"), Constraint("teg", "not in")),
            ),
        ),
        (
            Constraint("tegra", "in"),
            Constraint("rpi", "in"),
            (
                UnionConstraint(Constraint("tegra", "in"), Constraint("rpi", "in")),
                UnionConstraint(Constraint("rpi", "in"), Constraint("tegra", "in")),
            ),
        ),
        (
            Constraint("tegra", "not in"),
            Constraint("rpi", "not in"),
            AnyConstraint(),
        ),
        (
            Constraint("tegra", "in"),
            Constraint("1.2.3-tegra", "!="),
            AnyConstraint(),
        ),
        (
            Constraint("tegra", "not in"),
            Constraint("1.2.3-tegra", "!="),
            Constraint("1.2.3-tegra", "!="),
        ),
        (
            Constraint("tegra", "in"),
            Constraint("1.2.3-tegra", "=="),
            Constraint("tegra", "in"),
        ),
        (
            Constraint("tegra", "not in"),
            Constraint("1.2.3-tegra", "=="),
            (
                UnionConstraint(
                    Constraint("tegra", "not in"), Constraint("1.2.3-tegra", "==")
                ),
                UnionConstraint(
                    Constraint("1.2.3-tegra", "=="), Constraint("tegra", "not in")
                ),
            ),
        ),
    ],
)
def test_union(
    constraint1: BaseConstraint,
    constraint2: BaseConstraint,
    expected: BaseConstraint | tuple[BaseConstraint, BaseConstraint],
) -> None:
    if not isinstance(expected, tuple):
        expected = (expected, expected)

    assert constraint1.union(constraint2) == expected[0]
    assert constraint2.union(constraint1) == expected[1]


@pytest.mark.parametrize(
    ("constraint1", "constraint2", "expected"),
    [
        (
            EmptyConstraint(),
            ExtraConstraint("extra1"),
            ExtraConstraint("extra1"),
        ),
        (
            EmptyConstraint(),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
        ),
        (
            EmptyConstraint(),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
        ),
        (
            AnyConstraint(),
            ExtraConstraint("extra1"),
            AnyConstraint(),
        ),
        (
            AnyConstraint(),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
            AnyConstraint(),
        ),
        (
            AnyConstraint(),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            AnyConstraint(),
        ),
        (
            ExtraConstraint("extra1"),
            ExtraConstraint("extra1"),
            ExtraConstraint("extra1"),
        ),
        (
            ExtraConstraint("extra1"),
            ExtraConstraint("extra1", "!="),
            AnyConstraint(),
        ),
        (
            ExtraConstraint("extra1"),
            ExtraConstraint("extra2"),
            (
                UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
                UnionConstraint(ExtraConstraint("extra2"), ExtraConstraint("extra1")),
            ),
        ),
        (
            ExtraConstraint("extra1"),
            ExtraMultiConstraint(
                ExtraConstraint("extra2", "!="), ExtraConstraint("extra3", "!=")
            ),
            UnionConstraint(
                ExtraMultiConstraint(
                    ExtraConstraint("extra2", "!="), ExtraConstraint("extra3", "!=")
                ),
                ExtraConstraint("extra1"),
            ),
        ),
        (
            ExtraConstraint("extra1"),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
            UnionConstraint(ExtraConstraint("extra2", "!="), ExtraConstraint("extra1")),
        ),
        (
            ExtraConstraint("extra1"),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="),
                ExtraConstraint("extra2", "!="),
                ExtraConstraint("extra3", "!="),
            ),
            UnionConstraint(
                ExtraMultiConstraint(
                    ExtraConstraint("extra1", "!="),
                    ExtraConstraint("extra2", "!="),
                    ExtraConstraint("extra3", "!="),
                ),
                ExtraConstraint("extra1"),
            ),
        ),
        (
            ExtraConstraint("extra1"),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
        ),
        (
            ExtraConstraint("extra1"),
            UnionConstraint(ExtraConstraint("extra2"), ExtraConstraint("extra3")),
            (
                UnionConstraint(
                    ExtraConstraint("extra1"),
                    ExtraConstraint("extra2"),
                    ExtraConstraint("extra3"),
                ),
                UnionConstraint(
                    ExtraConstraint("extra2"),
                    ExtraConstraint("extra3"),
                    ExtraConstraint("extra1"),
                ),
            ),
        ),
        (
            ExtraConstraint("extra1"),
            ExtraConstraint("extra2", "!="),
            (
                UnionConstraint(
                    ExtraConstraint("extra1"), ExtraConstraint("extra2", "!=")
                ),
                UnionConstraint(
                    ExtraConstraint("extra2", "!="), ExtraConstraint("extra1")
                ),
            ),
        ),
        (
            ExtraConstraint("extra1", "!="),
            ExtraConstraint("extra2"),
            (
                UnionConstraint(
                    ExtraConstraint("extra1", "!="), ExtraConstraint("extra2")
                ),
                UnionConstraint(
                    ExtraConstraint("extra2"), ExtraConstraint("extra1", "!=")
                ),
            ),
        ),
        (
            ExtraConstraint("extra1", "!="),
            ExtraConstraint("extra2", "!="),
            (
                UnionConstraint(
                    ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
                ),
                UnionConstraint(
                    ExtraConstraint("extra2", "!="), ExtraConstraint("extra1", "!=")
                ),
            ),
        ),
        (
            ExtraConstraint("extra1", "!="),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
            ExtraConstraint("extra1", "!="),
        ),
        (
            ExtraConstraint("extra1", "!="),
            ExtraMultiConstraint(
                ExtraConstraint("extra2", "!="), ExtraConstraint("extra3", "!=")
            ),
            UnionConstraint(
                ExtraMultiConstraint(
                    ExtraConstraint("extra2", "!="), ExtraConstraint("extra3", "!=")
                ),
                ExtraConstraint("extra1", "!="),
            ),
        ),
        (
            ExtraConstraint("extra1", "!="),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            AnyConstraint(),
        ),
        (
            ExtraConstraint("extra1", "!="),
            UnionConstraint(ExtraConstraint("extra2"), ExtraConstraint("extra3")),
            (
                UnionConstraint(
                    ExtraConstraint("extra1", "!="),
                    ExtraConstraint("extra2"),
                    ExtraConstraint("extra3"),
                ),
                UnionConstraint(
                    ExtraConstraint("extra2"),
                    ExtraConstraint("extra3"),
                    ExtraConstraint("extra1", "!="),
                ),
            ),
        ),
        (
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
        ),
        (
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(ExtraConstraint("extra2"), ExtraConstraint("extra1")),
            (
                ExtraMultiConstraint(
                    ExtraConstraint("extra1"), ExtraConstraint("extra2")
                ),
                ExtraMultiConstraint(
                    ExtraConstraint("extra2"), ExtraConstraint("extra1")
                ),
            ),
        ),
        (
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
        ),
        (
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            UnionConstraint(ExtraConstraint("extra2"), ExtraConstraint("extra1")),
            (
                UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
                UnionConstraint(ExtraConstraint("extra2"), ExtraConstraint("extra1")),
            ),
        ),
        (
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra3")),
            (
                UnionConstraint(
                    ExtraConstraint("extra1"),
                    ExtraConstraint("extra2"),
                    ExtraConstraint("extra3"),
                ),
                UnionConstraint(
                    ExtraConstraint("extra1"),
                    ExtraConstraint("extra3"),
                    ExtraConstraint("extra2"),
                ),
            ),
        ),
        (
            UnionConstraint(
                ExtraConstraint("extra1"),
                ExtraConstraint("extra2"),
                ExtraConstraint("extra3"),
            ),
            UnionConstraint(
                ExtraConstraint("extra1"),
                ExtraConstraint("extra4"),
                ExtraConstraint("extra3"),
            ),
            (
                UnionConstraint(
                    ExtraConstraint("extra1"),
                    ExtraConstraint("extra2"),
                    ExtraConstraint("extra3"),
                    ExtraConstraint("extra4"),
                ),
                UnionConstraint(
                    ExtraConstraint("extra1"),
                    ExtraConstraint("extra4"),
                    ExtraConstraint("extra3"),
                    ExtraConstraint("extra2"),
                ),
            ),
        ),
        (
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra3", "!=")
            ),
            UnionConstraint(
                ExtraConstraint("extra1"),
                ExtraConstraint("extra2"),
                ExtraMultiConstraint(
                    ExtraConstraint("extra1", "!="), ExtraConstraint("extra3", "!=")
                ),
            ),
        ),
        (
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
            UnionConstraint(
                ExtraConstraint("extra1"),
                ExtraConstraint("extra2"),
                ExtraMultiConstraint(
                    ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
                ),
            ),
        ),
        (
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
        ),
        (
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(
                ExtraConstraint("extra1"),
                ExtraConstraint("extra2"),
                ExtraConstraint("extra3"),
            ),
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
        ),
        (
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra3")),
            (
                UnionConstraint(
                    ExtraMultiConstraint(
                        ExtraConstraint("extra1"), ExtraConstraint("extra2")
                    ),
                    ExtraMultiConstraint(
                        ExtraConstraint("extra1"), ExtraConstraint("extra3")
                    ),
                ),
                UnionConstraint(
                    ExtraMultiConstraint(
                        ExtraConstraint("extra1"), ExtraConstraint("extra3")
                    ),
                    ExtraMultiConstraint(
                        ExtraConstraint("extra1"), ExtraConstraint("extra2")
                    ),
                ),
            ),
        ),
        (
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
            ),
            ExtraMultiConstraint(
                ExtraConstraint("extra1", "!="), ExtraConstraint("extra3", "!=")
            ),
            (
                UnionConstraint(
                    ExtraMultiConstraint(
                        ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
                    ),
                    ExtraMultiConstraint(
                        ExtraConstraint("extra1", "!="), ExtraConstraint("extra3", "!=")
                    ),
                ),
                UnionConstraint(
                    ExtraMultiConstraint(
                        ExtraConstraint("extra1", "!="), ExtraConstraint("extra3", "!=")
                    ),
                    ExtraMultiConstraint(
                        ExtraConstraint("extra1", "!="), ExtraConstraint("extra2", "!=")
                    ),
                ),
            ),
        ),
        (
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
            ExtraMultiConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra3")),
            UnionConstraint(ExtraConstraint("extra1"), ExtraConstraint("extra2")),
        ),
    ],
)
def test_union_extra(
    constraint1: BaseConstraint,
    constraint2: BaseConstraint,
    expected: BaseConstraint | tuple[BaseConstraint, BaseConstraint],
) -> None:
    if not isinstance(expected, tuple):
        expected = (expected, expected)

    assert constraint1.union(constraint2) == expected[0]
    assert constraint2.union(constraint1) == expected[1]


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
