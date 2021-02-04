from pathlib import Path

import pytest

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.directory_dependency import DirectoryDependency


DIST_PATH = Path(__file__).parent.parent / "fixtures" / "git" / "github.com" / "demo"


def test_directory_dependency_must_exist():
    with pytest.raises(ValueError):
        DirectoryDependency("demo", DIST_PATH / "invalid")


def _test_directory_dependency_pep_508(name, path, pep_508_input, pep_508_output=None):
    dep = Dependency.create_from_pep_508(
        pep_508_input, relative_to=Path(__file__).parent
    )

    assert dep.is_directory()
    assert dep.name == name
    assert dep.path == path
    assert dep.to_pep_508() == pep_508_output or pep_508_input


def test_directory_dependency_pep_508_local_absolute():
    path = (
        Path(__file__).parent.parent
        / "fixtures"
        / "project_with_multi_constraints_dependency"
    )
    requirement = "{} @ file://{}".format("demo", path.as_posix())
    _test_directory_dependency_pep_508("demo", path, requirement)

    requirement = "{} @ {}".format("demo", path)
    _test_directory_dependency_pep_508("demo", path, requirement)


def test_directory_dependency_pep_508_localhost():
    path = (
        Path(__file__).parent.parent
        / "fixtures"
        / "project_with_multi_constraints_dependency"
    )
    requirement = "{} @ file://localhost{}".format("demo", path.as_posix())
    requirement_expected = "{} @ file://{}".format("demo", path.as_posix())
    _test_directory_dependency_pep_508("demo", path, requirement, requirement_expected)


def test_directory_dependency_pep_508_local_relative():
    path = Path("..") / "fixtures" / "project_with_multi_constraints_dependency"

    with pytest.raises(ValueError):
        requirement = "{} @ file://{}".format("demo", path.as_posix())
        _test_directory_dependency_pep_508("demo", path, requirement)

    requirement = "{} @ {}".format("demo", path)
    _test_directory_dependency_pep_508("demo", path, requirement)
