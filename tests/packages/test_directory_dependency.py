import pytest

from poetry.core.packages.directory_dependency import DirectoryDependency
from poetry.core.utils._compat import Path


DIST_PATH = Path(__file__).parent.parent / "fixtures" / "git" / "github.com" / "demo"


def test_directory_dependency_must_exist():
    with pytest.raises(ValueError):
        DirectoryDependency("demo", DIST_PATH / "invalid")
