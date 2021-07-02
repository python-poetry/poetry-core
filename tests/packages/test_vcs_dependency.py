import pytest

from poetry.core.packages.vcs_dependency import VCSDependency


def test_to_pep_508():
    dependency = VCSDependency(
        "poetry", "git", "https://github.com/python-poetry/poetry.git"
    )

    expected = "poetry @ git+https://github.com/python-poetry/poetry.git@master"

    assert expected == dependency.to_pep_508()


def test_to_pep_508_ssh():
    dependency = VCSDependency("poetry", "git", "git@github.com:sdispater/poetry.git")

    expected = "poetry @ git+ssh://git@github.com/sdispater/poetry.git@master"

    assert expected == dependency.to_pep_508()


def test_to_pep_508_with_extras():
    dependency = VCSDependency(
        "poetry", "git", "https://github.com/python-poetry/poetry.git", extras=["foo"]
    )

    expected = "poetry[foo] @ git+https://github.com/python-poetry/poetry.git@master"

    assert expected == dependency.to_pep_508()


def test_to_pep_508_in_extras():
    dependency = VCSDependency(
        "poetry", "git", "https://github.com/python-poetry/poetry.git"
    )
    dependency.in_extras.append("foo")

    expected = 'poetry @ git+https://github.com/python-poetry/poetry.git@master ; extra == "foo"'
    assert expected == dependency.to_pep_508()

    dependency = VCSDependency(
        "poetry", "git", "https://github.com/python-poetry/poetry.git", extras=["bar"]
    )
    dependency.in_extras.append("foo")

    expected = 'poetry[bar] @ git+https://github.com/python-poetry/poetry.git@master ; extra == "foo"'

    assert expected == dependency.to_pep_508()

    dependency = VCSDependency(
        "poetry", "git", "https://github.com/python-poetry/poetry.git", "b;ar;"
    )
    dependency.in_extras.append("foo;")

    expected = 'poetry @ git+https://github.com/python-poetry/poetry.git@b;ar; ; extra == "foo;"'

    assert expected == dependency.to_pep_508()


@pytest.mark.parametrize("groups", [["main"], ["dev"]])
def test_category(groups):
    dependency = VCSDependency(
        "poetry",
        "git",
        "https://github.com/python-poetry/poetry.git",
        groups=groups,
    )
    assert dependency.groups == frozenset(groups)


def test_vcs_dependency_can_have_resolved_reference_specified():
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
