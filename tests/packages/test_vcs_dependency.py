from __future__ import annotations

from typing import Any

import pytest

from packaging.utils import canonicalize_name

from poetry.core.packages.vcs_dependency import VCSDependency


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({}, "poetry @ git+https://github.com/python-poetry/poetry.git"),
        (
            {"extras": ["foo"]},
            "poetry[foo] @ git+https://github.com/python-poetry/poetry.git",
        ),
        (
            {"extras": ["foo", "bar"]},
            "poetry[bar,foo] @ git+https://github.com/python-poetry/poetry.git",
        ),
        (
            {"branch": "main"},
            "poetry @ git+https://github.com/python-poetry/poetry.git@main",
        ),
        (
            {"tag": "1.0"},
            "poetry @ git+https://github.com/python-poetry/poetry.git@1.0",
        ),
        (
            {"rev": "12345"},
            "poetry @ git+https://github.com/python-poetry/poetry.git@12345",
        ),
        (
            {"directory": "sub"},
            "poetry @ git+https://github.com/python-poetry/poetry.git#subdirectory=sub",
        ),
        (
            {"branch": "main", "directory": "sub"},
            (
                "poetry @ git+https://github.com/python-poetry/poetry.git"
                "@main#subdirectory=sub"
            ),
        ),
    ],
)
def test_to_pep_508(kwargs: dict[str, Any], expected: str) -> None:
    dependency = VCSDependency(
        "poetry", "git", "https://github.com/python-poetry/poetry.git", **kwargs
    )

    assert dependency.to_pep_508() == expected


def test_to_pep_508_ssh() -> None:
    dependency = VCSDependency("poetry", "git", "git@github.com:sdispater/poetry.git")

    expected = "poetry @ git+ssh://git@github.com/sdispater/poetry.git"

    assert dependency.to_pep_508() == expected


def test_to_pep_508_in_extras() -> None:
    dependency = VCSDependency(
        "poetry", "git", "https://github.com/python-poetry/poetry.git"
    )
    dependency.in_extras.append(canonicalize_name("foo"))

    expected = (
        'poetry @ git+https://github.com/python-poetry/poetry.git ; extra == "foo"'
    )
    assert dependency.to_pep_508() == expected

    dependency = VCSDependency(
        "poetry", "git", "https://github.com/python-poetry/poetry.git", extras=["bar"]
    )
    dependency.in_extras.append(canonicalize_name("foo"))

    expected = (
        'poetry[bar] @ git+https://github.com/python-poetry/poetry.git ; extra == "foo"'
    )

    assert dependency.to_pep_508() == expected

    dependency = VCSDependency(
        "poetry", "git", "https://github.com/python-poetry/poetry.git", "b;ar;"
    )
    dependency.in_extras.append(canonicalize_name("foo;"))

    expected = (
        "poetry @ git+https://github.com/python-poetry/poetry.git@b;ar; ; extra =="
        ' "foo;"'
    )

    assert dependency.to_pep_508() == expected


@pytest.mark.parametrize(
    "name,source,branch,extras,constraint,expected",
    [
        (
            "example",
            "https://example.org/example.git",
            "main",
            None,
            None,
            "example (*) @ git+https://example.org/example.git@main",
        ),
        (
            "example",
            "https://example.org/example.git",
            "main",
            ["foo"],
            "1.2",
            "example[foo] (1.2) @ git+https://example.org/example.git@main",
        ),
    ],
)
def test_directory_dependency_string_representation(
    name: str,
    source: str,
    branch: str,
    extras: list[str] | None,
    constraint: str | None,
    expected: str,
) -> None:
    dependency = VCSDependency(
        name=name, vcs="git", source=source, branch=branch, extras=extras
    )
    if constraint:
        dependency.constraint = constraint  # type: ignore[assignment]
    assert str(dependency) == expected


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
