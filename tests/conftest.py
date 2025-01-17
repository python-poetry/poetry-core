from __future__ import annotations

import os
import sys
import tempfile

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Callable

import pytest
import virtualenv

from poetry.core.factory import Factory
from poetry.core.utils._compat import WINDOWS


if TYPE_CHECKING:
    from collections.abc import Iterator

    from pytest import Config
    from pytest import Parser
    from pytest_mock import MockerFixture


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--integration",
        action="store_true",
        dest="integration",
        default=False,
        help="enable integration tests",
    )


def pytest_configure(config: Config) -> None:
    config.addinivalue_line("markers", "integration: mark integration tests")

    if not config.option.integration:
        config.option.markexpr = "not integration"


def get_project_from_dir(base_directory: Path) -> Callable[[str], Path]:
    def get(name: str) -> Path:
        path = base_directory / name
        if not path.exists():
            raise FileNotFoundError(str(path))
        return path

    return get


@pytest.fixture(scope="session")
def project_source_root() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def project_source_test_root() -> Path:
    return Path(__file__).parent


@pytest.fixture(scope="session")
def common_fixtures_directory(project_source_test_root: Path) -> Path:
    return project_source_test_root / "fixtures"


@pytest.fixture(scope="session")
def common_project(common_fixtures_directory: Path) -> Callable[[str], Path]:
    return get_project_from_dir(common_fixtures_directory)


@pytest.fixture(scope="session")
def masonry_fixtures_directory(project_source_test_root: Path) -> Path:
    return project_source_test_root / "masonry" / "builders" / "fixtures"


@pytest.fixture(scope="session")
def masonry_project(
    masonry_fixtures_directory: Path,
) -> Callable[[str], Path]:
    return get_project_from_dir(masonry_fixtures_directory)


@pytest.fixture
def temporary_directory() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="poetry-core") as tmp:
        yield Path(tmp)


@pytest.fixture
def venv(temporary_directory: Path) -> Path:
    venv_dir = temporary_directory / ".venv"
    virtualenv.cli_run(
        [
            "--no-download",
            "--no-periodic-update",
            "--python",
            sys.executable,
            venv_dir.as_posix(),
        ]
    )
    return venv_dir


@pytest.fixture
def python(venv: Path) -> str:
    return venv.joinpath("Scripts/Python.exe" if WINDOWS else "bin/python").as_posix()


@pytest.fixture()
def f() -> Factory:
    return Factory()


@pytest.fixture(autouse=True)
def with_mocked_get_vcs(mocker: MockerFixture) -> None:
    from poetry.core.vcs.git import Git

    mocker.patch(
        "poetry.core.vcs.git.Git.run", return_value="This is a mocked Git.run() output."
    )
    mocker.patch("poetry.core.vcs.get_vcs", return_value=Git())


@pytest.fixture(autouse=True)
def clear_env_source_date_epoch() -> None:
    """Clear SOURCE_DATE_EPOCH from environment to avoid non-deterministic failures"""
    if "SOURCE_DATE_EPOCH" in os.environ:
        del os.environ["SOURCE_DATE_EPOCH"]
