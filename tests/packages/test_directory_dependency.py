from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.directory_dependency import DirectoryDependency


DIST_PATH = Path(__file__).parent.parent / "fixtures" / "git" / "github.com" / "demo"
SAMPLE_PROJECT = Path(__file__).parent.parent / "fixtures" / "sample_project"


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
    assert dep.to_pep_508() == (pep_508_output or pep_508_input)


def test_directory_dependency_pep_508_local_absolute() -> None:
    path = (
        Path(__file__).parent.parent
        / "fixtures"
        / "project_with_multi_constraints_dependency"
    )
    expected = f"demo @ {path.as_uri()}"

    requirement = f"demo @ file://{path.as_posix()}"
    _test_directory_dependency_pep_508("demo", path, requirement, expected)

    requirement = f"demo @ {path}"
    _test_directory_dependency_pep_508("demo", path, requirement, expected)


def test_directory_dependency_pep_508_localhost() -> None:
    path = (
        Path(__file__).parent.parent
        / "fixtures"
        / "project_with_multi_constraints_dependency"
    )
    requirement = f"demo @ file://localhost{path.as_posix()}"
    expected = f"demo @ {path.as_uri()}"
    _test_directory_dependency_pep_508("demo", path, requirement, expected)


def test_directory_dependency_pep_508_local_relative() -> None:
    path = Path("..") / "fixtures" / "project_with_multi_constraints_dependency"

    with pytest.raises(ValueError):
        requirement = f"demo @ file://{path.as_posix()}"
        _test_directory_dependency_pep_508("demo", path, requirement)

    requirement = f"demo @ {path}"
    expected = f"demo @ {path.as_posix()}"
    _test_directory_dependency_pep_508("demo", path, requirement, expected)


def test_directory_dependency_pep_508_extras() -> None:
    path = (
        Path(__file__).parent.parent
        / "fixtures"
        / "project_with_multi_constraints_dependency"
    )
    requirement = f"demo[foo,bar] @ file://{path.as_posix()}"
    expected = f"demo[bar,foo] @ {path.as_uri()}"
    _test_directory_dependency_pep_508("demo", path, requirement, expected)


@pytest.mark.parametrize(
    "name,path,extras,constraint,expected",
    [
        (
            "my-package",
            SAMPLE_PROJECT,
            None,
            None,
            f"my-package (*) @ {SAMPLE_PROJECT.as_uri()}",
        ),
        (
            "my-package",
            SAMPLE_PROJECT,
            ["db"],
            "1.2",
            f"my-package[db] (1.2) @ {SAMPLE_PROJECT.as_uri()}",
        ),
    ],
)
def test_directory_dependency_string_representation(
    name: str,
    path: Path,
    extras: list[str] | None,
    constraint: str | None,
    expected: str,
) -> None:
    dependency = DirectoryDependency(name=name, path=path, extras=extras)
    if constraint:
        dependency.constraint = constraint  # type: ignore[assignment]
    assert str(dependency) == expected


@pytest.mark.parametrize(
    ("fixture", "name"),
    [
        ("project_with_pep517_non_poetry", "PEP 517"),
        ("project_with_setup_cfg_only", "setup.cfg"),
    ],
)
def test_directory_dependency_non_poetry_pep517(fixture: str, name: str) -> None:
    path = Path(__file__).parent.parent / "fixtures" / fixture

    try:
        DirectoryDependency("package", path)
    except ValueError as e:
        if "does not seem to be a Python package" not in str(e):
            raise e from e
        pytest.fail(f"A {name} project not recognized as valid directory dependency")
