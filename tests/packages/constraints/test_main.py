import pytest

from poetry.core.packages.constraints import parse_constraint
from poetry.core.packages.constraints.any_constraint import AnyConstraint
from poetry.core.packages.constraints.constraint import Constraint
from poetry.core.packages.constraints.multi_constraint import MultiConstraint
from poetry.core.packages.constraints.union_constraint import UnionConstraint


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
def test_parse_constraint(input, constraint):
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
        (
            'not in "x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE amd64 AMD64 win32 WIN32"',
            MultiConstraint(
                Constraint("x86_64", "!="),
                Constraint("X86_64", "!="),
                Constraint("aarch64", "!="),
                Constraint("AARCH64", "!="),
                Constraint("ppc64le", "!="),
                Constraint("PPC64LE", "!="),
                Constraint("amd64", "!="),
                Constraint("AMD64", "!="),
                Constraint("win32", "!="),
                Constraint("WIN32", "!="),
            )
        ),
    ],
)
def test_parse_constraint_multi(input, constraint):
    assert parse_constraint(input) == constraint


@pytest.mark.parametrize(
    "input,constraint",
    [
        ("win32 || linux", UnionConstraint(Constraint("win32"), Constraint("linux"))),
        (
            "win32 || !=linux2",
            UnionConstraint(Constraint("win32"), Constraint("linux2", "!=")),
        ),
        (
            'in "x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE amd64 AMD64 win32 WIN32"',
            UnionConstraint(
                Constraint("x86_64", "="),
                Constraint("X86_64", "="),
                Constraint("aarch64", "="),
                Constraint("AARCH64", "="),
                Constraint("ppc64le", "="),
                Constraint("PPC64LE", "="),
                Constraint("amd64", "="),
                Constraint("AMD64", "="),
                Constraint("win32", "="),
                Constraint("WIN32", "="),
            )
        ),
    ],
)
def test_parse_constraint_union(input, constraint):
    assert parse_constraint(input) == constraint
