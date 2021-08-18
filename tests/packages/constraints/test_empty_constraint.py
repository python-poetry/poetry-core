from poetry.core.packages.constraints.constraint import Constraint
from poetry.core.packages.constraints.empty_constraint import EmptyConstraint
from poetry.core.packages.constraints.multi_constraint import MultiConstraint
from poetry.core.packages.constraints.union_constraint import UnionConstraint


def test_allows():
    c = EmptyConstraint()

    assert c.allows(Constraint("win32"))
    assert c.allows(Constraint("linux"))
    assert c.allows(Constraint("darwin"))


def test_allows_any():
    c = EmptyConstraint()

    assert c.allows_any(Constraint("darwin"))
    assert c.allows_any(Constraint("darwin", "!="))
    assert c.allows_any(Constraint("win32"))
    assert c.allows_any(c)
    assert c.allows_any(
        MultiConstraint(Constraint("win32", "!="), Constraint("darwin", "!="))
    )


def test_allows_all():
    c = EmptyConstraint()

    assert c.allows_all(Constraint("darwin"))
    assert c.allows_all(Constraint("darwin", "!="))
    assert c.allows_all(Constraint("win32"))
    assert c.allows_all(c)
    assert c.allows_all(
        MultiConstraint(Constraint("win32", "!="), Constraint("darwin", "!="))
    )


def test_intersect():
    c = EmptyConstraint()

    intersection = c.intersect(Constraint("win32", "!="))
    assert intersection == Constraint("win32", "!=")


def test_union():
    c = EmptyConstraint()

    union = c.union(Constraint("linux"))
    assert union == Constraint("linux")

    union = c.union(UnionConstraint(Constraint("win32"), Constraint("linux")))
    assert union == UnionConstraint(Constraint("win32"), Constraint("linux"))

    union = c.union(UnionConstraint(Constraint("darwin"), Constraint("linux2")))
    assert union == UnionConstraint(Constraint("darwin"), Constraint("linux2"))


def test_difference():
    c = EmptyConstraint()

    assert c.difference(Constraint("win32")) is None
    assert c.difference(Constraint("linux")) is None


def test_is_any():
    c = EmptyConstraint()

    assert c.is_any() is False


def test_is_empty():
    c = EmptyConstraint()

    assert c.is_empty() is True
