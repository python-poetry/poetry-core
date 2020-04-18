import pytest

from pep517.check import check
from tests.utils import temporary_project_directory


pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "getter, project",
    [
        ("common_project", "simple_project"),
        ("masonry_project", "src_extended"),
        ("masonry_project", "disable_setup_py"),
    ],
)
def test_pep517_check(request, getter, project):
    with temporary_project_directory(request.getfixturevalue(getter)(project)) as path:
        assert check(path)
