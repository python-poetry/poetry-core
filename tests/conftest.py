from typing import Callable

import pytest

from poetry.core.utils._compat import Path


def get_project_from_dir(base_directory):  # type: (Path) -> Callable[[str], Path]
    def get(name):  # type: (str) -> Path
        path = base_directory / name
        if not path.exists():
            raise FileNotFoundError(str(path))
        return path

    return get


@pytest.fixture
def common_fixtures_directory():  # type: () -> Path
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def common_project(common_fixtures_directory):  # type: (Path) -> Callable[[str], Path]
    return get_project_from_dir(common_fixtures_directory)


@pytest.fixture
def masonry_fixtures_directory():  # type: () -> Path
    return Path(__file__).parent / "masonry" / "builders" / "fixtures"


@pytest.fixture
def masonry_project(
    masonry_fixtures_directory,
):  # type: (Path) -> Callable[[str], Path]
    return get_project_from_dir(masonry_fixtures_directory)
