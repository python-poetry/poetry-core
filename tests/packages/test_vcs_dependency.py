from __future__ import annotations

import pytest

from poetry.core.packages.vcs_dependency import VCSDependency


def test_to_pep_508() -> None:
    dependency = VCSDependency(
        "poetry", "git", "https://github.com/python-poetry/poetry.git"
    )

    expected = "poetry @ git+https://github.com/python-poetry/poetry.git"

    assert dependency.to_pep_508() == expected


def test_to_pep_508_ssh() -> None:
    dependency = VCSDependency("poetry", "git", "git@github.com:sdispater/poetry.git")

    expected = "poetry @ git+ssh://git@github.com/sdispater/poetry.git"

    assert dependency.to_pep_508() == expected


def test_to_pep_508_with_extras() -> None:
    dependency = VCSDependency(
        "poetry",
        "git",
        "https://github.com/python-poetry/poetry.git",
        extras=["foo", "bar"],
    )

    expected = "poetry[bar,foo] @ git+https://github.com/python-poetry/poetry.git"

    assert dependency.to_pep_508() == expected


def test_to_pep_508_in_extras() -> None:
    dependency = VCSDependency(
        "poetry", "git", "https://github.com/python-poetry/poetry.git"
    )
    dependency.in_extras.append("foo")

    expected = (
        'poetry @ git+https://github.com/python-poetry/poetry.git ; extra == "foo"'
    )
    assert dependency.to_pep_508() == expected

    dependency = VCSDependency(
        "poetry", "git", "https://github.com/python-poetry/poetry.git", extras=["bar"]
    )
    dependency.in_extras.append("foo")

    expected = (
        'poetry[bar] @ git+https://github.com/python-poetry/poetry.git ; extra == "foo"'
    )

    assert dependency.to_pep_508() == expected

    dependency = VCSDependency(
        "poetry", "git", "https://github.com/python-poetry/poetry.git", "b;ar;"
    )
    dependency.in_extras.append("foo;")

    expected = (
        "poetry @ git+https://github.com/python-poetry/poetry.git@b;ar; ; extra =="
        ' "foo;"'
    )

    assert dependency.to_pep_508() == expected


@pytest.mark.parametrize("groups", [["main"], ["dev"]])
def test_category(groups: list[str]) -> None:
    dependency = VCSDependency(
        "poetry",
        "git",
        "https://github.com/python-poetry/poetry.git",
        groups=groups,
    )
    assert dependency.groups == frozenset(groups)


def test_vcs_dependency_can_have_resolved_reference_specified() -> None:
    dependency = VCSDependency(
        "poetry",
        "git",
        "https://github.com/python-poetry/poetry.git",
        branch="develop",
        resolved_rev="123456",
    )

    assert dependency.branch == "develop"
    assert dependency.source_reference == "develop"
    assert dependency.source_resolved_reference == "123456"


def test_vcs_dependencies_are_equal_if_resolved_references_match() -> None:
    dependency1 = VCSDependency(
        "poetry",
        "git",
        "https://github.com/python-poetry/poetry.git",
        branch="develop",
        resolved_rev="123456",
    )
    dependency2 = VCSDependency(
        "poetry",
        "git",
        "https://github.com/python-poetry/poetry.git",
        rev="123",
        resolved_rev="123456",
    )

    assert dependency1 == dependency2
