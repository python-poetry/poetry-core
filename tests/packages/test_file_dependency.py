from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from typing import cast

import pytest

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.file_dependency import FileDependency
from poetry.core.version.markers import SingleMarker


if TYPE_CHECKING:
    from pytest import LogCaptureFixture
    from pytest_mock import MockerFixture

    from poetry.core.version.markers import BaseMarker

DIST_PATH = Path(__file__).parent.parent / "fixtures" / "distributions"
TEST_FILE = "demo-0.1.0.tar.gz"


def test_file_dependency_does_not_exist(
    caplog: LogCaptureFixture, mocker: MockerFixture
) -> None:
    mock_exists = mocker.patch.object(Path, "exists")
    mock_exists.return_value = False
    dep = FileDependency("demo", DIST_PATH / "demo-0.2.0.tar.gz")
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "WARNING"
    assert "does not exist" in record.message

    with pytest.raises(ValueError, match="does not exist"):
        dep.validate(raise_error=True)

    mock_exists.assert_called_once()


def test_file_dependency_is_directory(
    caplog: LogCaptureFixture, mocker: MockerFixture
) -> None:
    mock_is_directory = mocker.patch.object(Path, "is_dir")
    mock_is_directory.return_value = True
    dep = FileDependency("demo", DIST_PATH)
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "WARNING"
    assert "is a directory" in record.message

    with pytest.raises(ValueError, match="is a directory"):
        dep.validate(raise_error=True)

    mock_is_directory.assert_called_once()


def _test_file_dependency_pep_508(
    mocker: MockerFixture,
    name: str,
    path: Path,
    pep_508_input: str,
    pep_508_output: str | None = None,
    marker: BaseMarker | None = None,
) -> None:
    mocker.patch.object(Path, "exists").return_value = True
    mocker.patch.object(Path, "is_file").return_value = True

    dep = Dependency.create_from_pep_508(
        pep_508_input, relative_to=Path(__file__).parent
    )
    if marker:
        dep.marker = marker

    assert dep.is_file()
    dep = cast("FileDependency", dep)
    assert dep.name == name
    assert dep.path == path
    assert dep.to_pep_508() == (pep_508_output or pep_508_input)


def test_file_dependency_pep_508_local_file_absolute(mocker: MockerFixture) -> None:
    path = DIST_PATH / "demo-0.2.0.tar.gz"
    expected = f"demo @ {path.as_uri()}"

    requirement = f"demo @ file://{path.as_posix()}"
    _test_file_dependency_pep_508(mocker, "demo", path, requirement, expected)

    requirement = f"demo @ {path}"
    _test_file_dependency_pep_508(mocker, "demo", path, requirement, expected)


def test_file_dependency_pep_508_local_file_localhost(mocker: MockerFixture) -> None:
    path = DIST_PATH / "demo-0.2.0.tar.gz"
    requirement = f"demo @ file://localhost{path.as_posix()}"
    expected = f"demo @ {path.as_uri()}"
    _test_file_dependency_pep_508(mocker, "demo", path, requirement, expected)


def test_file_dependency_pep_508_local_file_relative_path(
    mocker: MockerFixture,
) -> None:
    path = Path("..") / "fixtures" / "distributions" / "demo-0.2.0.tar.gz"

    with pytest.raises(ValueError):
        requirement = f"demo @ file://{path.as_posix()}"
        _test_file_dependency_pep_508(mocker, "demo", path, requirement)

    requirement = f"demo @ {path}"
    base = Path(__file__).parent
    expected = f"demo @ {(base / path).resolve().as_uri()}"
    _test_file_dependency_pep_508(mocker, "demo", path, requirement, expected)


def test_file_dependency_pep_508_with_subdirectory(mocker: MockerFixture) -> None:
    path = DIST_PATH / "demo.zip"
    expected = f"demo @ {path.as_uri()}#subdirectory=sub"

    requirement = f"demo @ file://{path.as_posix()}#subdirectory=sub"
    _test_file_dependency_pep_508(mocker, "demo", path, requirement, expected)


def test_to_pep_508_with_marker(mocker: MockerFixture) -> None:
    wheel = "demo-0.1.0-py2.py3-none-any.whl"

    abs_path = DIST_PATH / wheel
    requirement = f'demo @ {abs_path.as_uri()} ; sys_platform == "linux"'
    _test_file_dependency_pep_508(
        mocker,
        "demo",
        abs_path,
        requirement,
        marker=SingleMarker("sys.platform", "linux"),
    )


def test_relative_file_dependency_to_pep_508_with_marker(mocker: MockerFixture) -> None:
    wheel = "demo-0.1.0-py2.py3-none-any.whl"

    rel_path = Path("..") / "fixtures" / "distributions" / wheel
    requirement = f'demo @ {rel_path.as_posix()} ; sys_platform == "linux"'
    base = Path(__file__).parent
    expected = (
        f'demo @ {(base / rel_path).resolve().as_uri()} ; sys_platform == "linux"'
    )
    _test_file_dependency_pep_508(
        mocker,
        "demo",
        rel_path,
        requirement,
        expected,
        marker=SingleMarker("sys.platform", "linux"),
    )


def test_file_dependency_pep_508_extras(mocker: MockerFixture) -> None:
    wheel = "demo-0.1.0-py2.py3-none-any.whl"

    rel_path = Path("..") / "fixtures" / "distributions" / wheel
    requirement = f'demo[foo,bar] @ {rel_path.as_posix()} ; sys_platform == "linux"'
    base = Path(__file__).parent
    expected = (
        f"demo[bar,foo] @ {(base / rel_path).resolve().as_uri()} ;"
        ' sys_platform == "linux"'
    )
    _test_file_dependency_pep_508(
        mocker,
        "demo",
        rel_path,
        requirement,
        expected,
    )


@pytest.mark.parametrize(
    "name,path,extras,constraint,expected",
    [
        (
            "demo",
            DIST_PATH / TEST_FILE,
            None,
            None,
            f"demo (*) @ {(DIST_PATH / TEST_FILE).as_uri()}",
        ),
        (
            "demo",
            DIST_PATH / TEST_FILE,
            ["foo"],
            "1.2",
            f"demo[foo] (1.2) @ {(DIST_PATH / TEST_FILE).as_uri()}",
        ),
    ],
)
def test_file_dependency_string_representation(
    name: str,
    path: Path,
    extras: list[str] | None,
    constraint: str | None,
    expected: str,
) -> None:
    dependency = FileDependency(name=name, path=path, extras=extras)
    if constraint:
        dependency.constraint = constraint  # type: ignore[assignment]
    assert str(dependency) == expected
