from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from typing import cast

import pytest

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.directory_dependency import DirectoryDependency


if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from pytest_mock import MockerFixture


DIST_PATH = Path(__file__).parent.parent / "fixtures" / "distributions"
SAMPLE_PROJECT = Path(__file__).parent.parent / "fixtures" / "sample_project"


def test_directory_dependency_does_not_exist(
    caplog: LogCaptureFixture, mocker: MockerFixture
) -> None:
    mock_exists = mocker.patch.object(Path, "exists")
    mock_exists.return_value = False
    dep = DirectoryDependency("demo", DIST_PATH / "invalid")
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "WARNING"
    assert "does not exist" in record.message

    with pytest.raises(ValueError, match="does not exist"):
        dep.validate(raise_error=True)

    mock_exists.assert_called_once()


def test_directory_dependency_is_file(
    caplog: LogCaptureFixture, mocker: MockerFixture
) -> None:
    mock_is_file = mocker.patch.object(Path, "is_file")
    mock_is_file.return_value = True
    dep = DirectoryDependency("demo", DIST_PATH / "demo-0.1.0.tar.gz")
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "WARNING"
    assert "is a file" in record.message

    with pytest.raises(ValueError, match="is a file"):
        dep.validate(raise_error=True)

    mock_is_file.assert_called_once()


def test_directory_dependency_is_not_a_python_project(
    caplog: LogCaptureFixture,
) -> None:
    dep = DirectoryDependency("demo", DIST_PATH)
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "WARNING"
    assert "a Python package" in record.message

    with pytest.raises(ValueError, match="not .* a Python package"):
        dep.validate(raise_error=True)


def _test_directory_dependency_pep_508(
    name: str, path: Path, pep_508_input: str, pep_508_output: str | None = None
) -> None:
    dep = Dependency.create_from_pep_508(
        pep_508_input, relative_to=Path(__file__).parent
    )

    assert dep.is_directory()
    dep = cast("DirectoryDependency", dep)
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
    base = Path(__file__).parent
    expected = f"demo @ {(base / path).resolve().as_uri()}"
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


def test_directory_dependency_pep_508_with_marker() -> None:
    path = (
        Path(__file__).parent.parent
        / "fixtures"
        / "project_with_multi_constraints_dependency"
    )
    requirement = f'demo @ file://{path.as_posix()} ; sys_platform == "linux"'
    expected = f'demo @ {path.as_uri()} ; sys_platform == "linux"'
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
