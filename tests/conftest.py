from __future__ import annotations

import shutil
import sys
import tempfile

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Callable
from typing import Iterator

import pytest
import virtualenv

from poetry.core.factory import Factory
from poetry.core.utils._compat import WINDOWS


if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.fixtures import FixtureRequest

    from tests.types import FixtureFactory


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


@pytest.fixture
def fixture_factory(request: FixtureRequest, tmp_path: Path) -> FixtureFactory:
    """Provides a factory function that creates a copy of a fixture in a temporary directory."""
    test_root = Path(__file__).parent

    def _factory(name: str, scope: Path | None = None) -> Path:
        if scope is None:
            # If scope is None, find "fixtures/" relative to the test.
            scope = request.path.parent.relative_to(test_root)

        source = test_root / scope / "fixtures" / name
        target = tmp_path / name

        if not source.exists():
            raise FileNotFoundError(source)

        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copyfile(source, target)

        return target

    return _factory


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
