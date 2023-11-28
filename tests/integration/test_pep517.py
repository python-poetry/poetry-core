from __future__ import annotations

import functools
import subprocess
import sys

from pathlib import Path
from typing import Any, Callable, TYPE_CHECKING

import pytest


# noinspection PyProtectedMember
from build.__main__ import build_package
from build.util import project_wheel_metadata

from tests.testutils import subprocess_run
from tests.testutils import temporary_project_directory


if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest

pytestmark = pytest.mark.integration


def verbose_called_process_error(test_function: Callable[..., None]) -> Callable[..., None]:
    """Decorator to emit verbose CalledProcessError details on stderr."""

    @functools.wraps(test_function)
    def verbose_called_process_error_wrapper(*args: Any, **kwargs: Any) -> None:
        try:
            return test_function(*args, **kwargs)
        except subprocess.CalledProcessError as error:
            try:
                stdout = error.stdout.decode('utf-8')
            except UnicodeError:
                stdout = error.stdout
            try:
                stderr = error.stderr.decode('utf-8')
            except UnicodeError:
                stderr = error.stderr
            sys.stderr.write("\n---=============---\n")
            sys.stderr.write(
                "CalledProcessError details (test fixtures can swallow it):\n"
            )
            sys.stderr.write(f"stdout = {stdout}\n")
            sys.stderr.write(f"stderr = {stderr}\n")
            sys.stderr.write("---=============---\n")
            raise

    return verbose_called_process_error_wrapper


@verbose_called_process_error
@pytest.mark.parametrize(
    "getter, project",
    [
        ("common_project", "simple_project"),
        ("masonry_project", "src_extended"),
        ("masonry_project", "disable_setup_py"),
    ],
)
def test_pep517_check_poetry_managed(
    request: FixtureRequest, getter: str, project: str
) -> None:
    with temporary_project_directory(request.getfixturevalue(getter)(project)) as path:
        assert project_wheel_metadata(path)


@verbose_called_process_error
def test_pep517_check(project_source_root: Path) -> None:
    assert project_wheel_metadata(str(project_source_root))


@verbose_called_process_error
def test_pep517_build_sdist(
    temporary_directory: Path, project_source_root: Path
) -> None:
    build_package(
        srcdir=str(project_source_root),
        outdir=str(temporary_directory),
        distributions=["sdist"],
    )
    distributions = list(temporary_directory.glob("poetry_core-*.tar.gz"))
    assert len(distributions) == 1


@verbose_called_process_error
def test_pep517_build_wheel(
    temporary_directory: Path, project_source_root: Path
) -> None:
    build_package(
        srcdir=str(project_source_root),
        outdir=str(temporary_directory),
        distributions=["wheel"],
    )
    distributions = list(temporary_directory.glob("poetry_core-*-none-any.whl"))
    assert len(distributions) == 1


@verbose_called_process_error
def test_pip_wheel_build(temporary_directory: Path, project_source_root: Path) -> None:
    tmp = str(temporary_directory)
    pip = subprocess_run(
        "pip", "wheel", "--use-pep517", "-w", tmp, str(project_source_root)
    )
    assert "Successfully built poetry-core" in pip.stdout

    assert pip.returncode == 0

    wheels = list(Path(tmp).glob("poetry_core-*-none-any.whl"))
    assert len(wheels) == 1


@verbose_called_process_error
def test_pip_install_no_binary(python: str, project_source_root: Path) -> None:
    subprocess_run(
        python,
        "-m",
        "pip",
        "install",
        "--no-binary",
        ":all:",
        project_source_root.as_posix(),
    )

    pip_show = subprocess_run(python, "-m", "pip", "show", "poetry-core")
    assert "Name: poetry-core" in pip_show.stdout
