import sys

from pathlib import Path
from typing import Callable

import pytest
import virtualenv

from poetry.core.factory import Factory
from tests.testutils import tempfile


def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true",
        dest="integration",
        default=False,
        help="enable integration tests",
    )


def pytest_configure(config):
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
def temporary_directory() -> Path:
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
    return (venv / "bin" / "python").as_posix()


@pytest.fixture()
def f() -> Factory:
    return Factory()
