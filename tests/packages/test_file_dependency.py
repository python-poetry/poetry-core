from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from typing import cast

import pytest

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.file_dependency import FileDependency
from poetry.core.version.markers import SingleMarker


if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
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


def test_default_hash() -> None:
    with pytest.warns(DeprecationWarning):
        path = DIST_PATH / TEST_FILE
        dep = FileDependency("demo", path)
        sha_256 = "72e8531e49038c5f9c4a837b088bfcb8011f4a9f76335c8f0654df6ac539b3d6"
        assert dep.hash() == sha_256


try:
    from hashlib import algorithms_guaranteed
except ImportError:
    algorithms_guaranteed = {"md5", "sha1", "sha224", "sha256", "sha384", "sha512"}


@pytest.mark.parametrize(
    "hash_name,expected",
    [
        (hash_name, value)
        for hash_name, value in [
            ("sha224", "972d02f36539a98599aed0566bc8aaf3e6701f4e895dd797d8f5248e"),
            (
                "sha3_512",
                "c04ee109ae52d6440445e24dbd6d244a1d0f0289ef79cb7ba9bc3c139c0237169af9a8f61cd1cf4fc17f853ddf84f97c475ac5bb6c91a4aff0b825b884d4896c",
            ),
            (
                "blake2s",
                "c336ecbc9d867c9d860accfba4c3723c51c4b5c47a1e0a955e1c8df499e36741",
            ),
            (
                "sha3_384",
                "d4abb2459941369aabf8880c5287b7eeb80678e14f13c71b9ecf64c772029dc3f93939590bea9ecdb51a1d1a74fefc5a",
            ),
            (
                "blake2b",
                "48e70abac547ab38e2330e6e6743a0c0f6274dcaa6df2c98135a78a9dd5b04a072d551fc3851b34da03eb0bf50dd71c7f32a8c36956e99fd6c66491bc7844800",
            ),
            (
                "sha256",
                "72e8531e49038c5f9c4a837b088bfcb8011f4a9f76335c8f0654df6ac539b3d6",
            ),
            (
                "sha512",
                "e08a00a4b86358e49a318e7e3ba7a3d2fabdd17a2fef95559a0af681ea07ab1296b0b8e11e645297da296290661dc07ae3c8f74eab66bd18a80dce0c0ccb355b",
            ),
            (
                "sha384",
                "aa3144e28c6700a83247e8ec8711af5d3f5f75997990d48ec41e66bd275b3d0e19ee6f2fe525a358f874aa717afd06a9",
            ),
            ("sha3_224", "64bfc6e4125b4c6d67fd88ad1c7d1b5c4dc11a1970e433cd576c91d4"),
            ("sha1", "4c057579005ac3e68e951a11ffdc4b27c6ae16af"),
            (
                "sha3_256",
                "ba3d2a964b0680b6dc9565a03952e29c294c785d5a2307d3e2d785d73b75ed7e",
            ),
        ]
        if hash_name in algorithms_guaranteed
    ],
)
def test_guaranteed_hash(hash_name: str, expected: str) -> None:
    with pytest.warns(DeprecationWarning):
        path = DIST_PATH / TEST_FILE
        dep = FileDependency("demo", path)
        assert dep.hash(hash_name) == expected


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
