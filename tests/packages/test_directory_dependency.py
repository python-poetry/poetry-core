from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.directory_dependency import DirectoryDependency


DIST_PATH = Path(__file__).parent.parent / "fixtures" / "git" / "github.com" / "demo"


def test_directory_dependency_must_exist() -> None:
    with pytest.raises(ValueError):
        DirectoryDependency("demo", DIST_PATH / "invalid")


def _test_directory_dependency_pep_508(
    name: str, path: Path, pep_508_input: str, pep_508_output: str | None = None
) -> None:
    dep = Dependency.create_from_pep_508(
        pep_508_input, relative_to=Path(__file__).parent
    )

    assert dep.is_directory()
    dep = cast(DirectoryDependency, dep)
    assert dep.name == name
    assert dep.path == path
    assert dep.to_pep_508() == pep_508_output or pep_508_input


def test_directory_dependency_pep_508_local_absolute() -> None:
    path = (
        Path(__file__).parent.parent
        / "fixtures"
        / "project_with_multi_constraints_dependency"
    )
    requirement = f"demo @ file://{path.as_posix()}"
    _test_directory_dependency_pep_508("demo", path, requirement)

    requirement = f"demo @ {path}"
    _test_directory_dependency_pep_508("demo", path, requirement)


def test_directory_dependency_pep_508_localhost() -> None:
    path = (
        Path(__file__).parent.parent
        / "fixtures"
        / "project_with_multi_constraints_dependency"
    )
    requirement = f"demo @ file://localhost{path.as_posix()}"
    requirement_expected = f"demo @ file://{path.as_posix()}"
    _test_directory_dependency_pep_508("demo", path, requirement, requirement_expected)


def test_directory_dependency_pep_508_local_relative() -> None:
    path = Path("..") / "fixtures" / "project_with_multi_constraints_dependency"

    with pytest.raises(ValueError):
        requirement = f"demo @ file://{path.as_posix()}"
        _test_directory_dependency_pep_508("demo", path, requirement)

    requirement = f"demo @ {path}"
    _test_directory_dependency_pep_508("demo", path, requirement)


def test_directory_dependency_pep_508_extras() -> None:
    path = (
        Path(__file__).parent.parent
        / "fixtures"
        / "project_with_multi_constraints_dependency"
    )
    requirement = f"demo[foo,bar] @ file://{path.as_posix()}"
    requirement_expected = f"demo[bar,foo] @ file://{path.as_posix()}"
    _test_directory_dependency_pep_508("demo", path, requirement, requirement_expected)
