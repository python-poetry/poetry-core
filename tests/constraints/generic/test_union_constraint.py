from __future__ import annotations

from poetry.core.constraints.generic import Constraint
from poetry.core.constraints.generic import UnionConstraint


def test_allows() -> None:
    c = UnionConstraint(Constraint("win32"), Constraint("linux"))

    assert c.allows(Constraint("win32"))
    assert c.allows(Constraint("linux"))
    assert not c.allows(Constraint("darwin"))


def test_allows_any() -> None:
    c = UnionConstraint(Constraint("win32"), Constraint("linux"))

    assert c.allows_any(c)
    assert c.allows_any(UnionConstraint(Constraint("win32"), Constraint("darwin")))
    assert not c.allows_any(UnionConstraint(Constraint("linux2"), Constraint("darwin")))
    assert c.allows_any(Constraint("win32"))
    assert not c.allows_any(Constraint("darwin"))


def test_allows_all() -> None:
    c = UnionConstraint(Constraint("win32"), Constraint("linux"))

    assert c.allows_all(c)
    assert not c.allows_all(UnionConstraint(Constraint("win32"), Constraint("darwin")))
    assert not c.allows_all(UnionConstraint(Constraint("linux2"), Constraint("darwin")))
    assert c.allows_all(Constraint("win32"))
    assert not c.allows_all(Constraint("darwin"))
