from __future__ import annotations

import shutil

from pathlib import Path

import pytest

from build.__main__ import build_package

from tests.testutils import subprocess_run


pytestmark = pytest.mark.integration


BUILD_SYSTEM_TEMPLATE = """
[build-system]
requires = ["poetry-core @ file://{project_path}"{additional_requires}]
build-backend = "poetry.core.masonry.api"
"""


def test_pip_install(
    temporary_directory: Path, project_source_root: Path, python: str
) -> None:
    """
    Ensure that a project using the repository version of poetry-core as a PEP 517 backend can be built.
    """
    temp_pep_517_backend_path = temporary_directory / "pep_517_backend"

    # Copy `pep_517_backend` to a temporary directory as we need to dynamically add the
    # build system during the test. This ensures that we don't update the source, since
    # the value of `requires` is dynamic.
    shutil.copytree(
        Path(__file__).parent.parent / "fixtures/pep_517_backend",
        temp_pep_517_backend_path,
    )

    # Append dynamic `build-system` section to `pyproject.toml` in the temporary
    # project directory.
    with open(temp_pep_517_backend_path / "pyproject.toml", "a") as f:
        f.write(
            BUILD_SYSTEM_TEMPLATE.format(
                project_path=project_source_root.as_posix(),
                additional_requires="",
            )
        )

    subprocess_run(
        python,
        "-m",
        "pip",
        "install",
        temp_pep_517_backend_path.as_posix(),
    )

    pip_show = subprocess_run(python, "-m", "pip", "show", "foo")
    assert "Name: foo" in pip_show.stdout


def test_pep517_build_wheel_build_script(
    temporary_directory: Path,
    project_source_root: Path,
    common_fixtures_directory: Path,
) -> None:
    temp_pep_517_backend_path = temporary_directory / "pep_517_backend"

    # Copy `pep_517_backend` to a temporary directory as we need to dynamically add the
    # build system during the test. This ensures that we don't update the source, since
    # the value of `requires` is dynamic.
    shutil.copytree(
        common_fixtures_directory / "pep_517_backend_build_script",
        temp_pep_517_backend_path,
    )

    # Append dynamic `build-system` section to `pyproject.toml` in the temporary
    # project directory.
    with open(temp_pep_517_backend_path / "pyproject.toml", "a") as f:
        f.write(
            BUILD_SYSTEM_TEMPLATE.format(
                project_path=project_source_root.as_posix(),
                additional_requires=', "setuptools"',
            )
        )

    build_package(
        srcdir=str(temp_pep_517_backend_path),
        outdir=str(temporary_directory),
        distributions=["wheel"],
    )
    distributions = list(temporary_directory.glob("foo-1.2.3-cp*-cp*-*.whl"))
    print(list(temporary_directory.iterdir()))
    assert len(distributions) == 1
    whl = distributions[0]
    assert whl.stem.rsplit("-")[-1] == "dummy"
