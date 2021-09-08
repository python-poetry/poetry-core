from contextlib import contextmanager
from io import BytesIO
from pathlib import Path

import pytest

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.file_dependency import FileDependency
from poetry.core.version.markers import SingleMarker


DIST_PATH = Path(__file__).parent.parent / "fixtures" / "distributions"


def test_file_dependency_wrong_path():
    with pytest.raises(ValueError):
        FileDependency("demo", DIST_PATH / "demo-0.2.0.tar.gz")


def test_file_dependency_dir():
    with pytest.raises(ValueError):
        FileDependency("demo", DIST_PATH)


def _test_file_dependency_pep_508(
    mocker, name, path, pep_508_input, pep_508_output=None, marker=None
):
    mocker.patch.object(Path, "exists").return_value = True
    mocker.patch.object(Path, "is_file").return_value = True

    dep = Dependency.create_from_pep_508(
        pep_508_input, relative_to=Path(__file__).parent
    )
    if marker:
        dep.marker = marker

    assert dep.is_file()
    assert dep.name == name
    assert dep.path == path
    assert dep.to_pep_508() == pep_508_output or pep_508_input


def test_file_dependency_pep_508_local_file_absolute(mocker):
    path = DIST_PATH / "demo-0.2.0.tar.gz"
    requirement = "{} @ file://{}".format("demo", path.as_posix())
    _test_file_dependency_pep_508(mocker, "demo", path, requirement)

    requirement = "{} @ {}".format("demo", path)
    _test_file_dependency_pep_508(mocker, "demo", path, requirement)


def test_file_dependency_pep_508_local_file_localhost(mocker):
    path = DIST_PATH / "demo-0.2.0.tar.gz"
    requirement = "{} @ file://localhost{}".format("demo", path.as_posix())
    requirement_expected = "{} @ file://{}".format("demo", path.as_posix())
    _test_file_dependency_pep_508(
        mocker, "demo", path, requirement, requirement_expected
    )


def test_file_dependency_pep_508_local_file_relative_path(mocker):
    path = Path("..") / "fixtures" / "distributions" / "demo-0.2.0.tar.gz"

    with pytest.raises(ValueError):
        requirement = "{} @ file://{}".format("demo", path.as_posix())
        _test_file_dependency_pep_508(mocker, "demo", path, requirement)

    requirement = "{} @ {}".format("demo", path)
    _test_file_dependency_pep_508(mocker, "demo", path, requirement)


def test_absolute_file_dependency_to_pep_508_with_marker(mocker):
    wheel = "demo-0.1.0-py2.py3-none-any.whl"

    abs_path = DIST_PATH / wheel
    requirement = '{} @ file://{} ; sys_platform == "linux"'.format(
        "demo", abs_path.as_posix()
    )
    _test_file_dependency_pep_508(
        mocker,
        "demo",
        abs_path,
        requirement,
        marker=SingleMarker("sys.platform", "linux"),
    )


def test_relative_file_dependency_to_pep_508_with_marker(mocker):
    wheel = "demo-0.1.0-py2.py3-none-any.whl"

    rel_path = Path("..") / "fixtures" / "distributions" / wheel
    requirement = '{} @ {} ; sys_platform == "linux"'.format(
        "demo", rel_path.as_posix()
    )
    _test_file_dependency_pep_508(
        mocker,
        "demo",
        rel_path,
        requirement,
        marker=SingleMarker("sys.platform", "linux"),
    )


@pytest.mark.parametrize(
    "algorithm, content, file_hash",
    [
        (
            "sha256",
            b"file contents",
            "7bb6f9f7a47a63e684925af3608c059edcc371eb81188c48c9714896fb1091fd",
        ),
        ("md5", b"file contents", "4a8ec4fa5f01b4ab1a0ab8cbccb709f0"),
    ],
)
def test_file_dependency_hash(mocker, algorithm, content, file_hash):
    @contextmanager
    def mock_file_contents(*_):
        yield BytesIO(content)

    path = DIST_PATH / "demo-0.2.0.tar.gz"
    mocker.patch.object(Path, "exists").return_value = True
    mocker.patch.object(Path, "is_file").return_value = True
    mocker.patch.object(Path, "open", mock_file_contents)

    file_dep = FileDependency("demo", path)
    assert file_dep.hash(algorithm) == file_hash
