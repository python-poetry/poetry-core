from __future__ import annotations

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.dependency_group import DependencyGroup


def test_dependency_group_remove_dependency() -> None:
    group = DependencyGroup(name="linter")
    group.add_dependency(Dependency(name="black", constraint="*"))
    group.add_dependency(Dependency(name="isort", constraint="*"))
    group.add_dependency(Dependency(name="flake8", constraint="*"))

    assert {dependency.name for dependency in group.dependencies} == {
        "black",
        "isort",
        "flake8",
    }

    group.remove_dependency("isort")
    assert {dependency.name for dependency in group.dependencies} == {"black", "flake8"}

    group.remove_dependency("black")
    assert {dependency.name for dependency in group.dependencies} == {"flake8"}

    group.remove_dependency("flake8")
    assert {dependency.name for dependency in group.dependencies} == set()
