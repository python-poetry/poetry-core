import pytest

from pep517.check import check
from tests.utils import temporary_project_directory


pytestmark = pytest.mark.integration


def test_pep517_simple_project(common_project):
    with temporary_project_directory(common_project("simple_project")) as path:
        assert check(path)


def test_pep517_src_extended(masonry_project):
    with temporary_project_directory(masonry_project("src_extended")) as path:
        assert check(path)


def test_pep517_disable_setup_py(masonry_project):
    with temporary_project_directory(masonry_project("disable_setup_py")) as path:
        assert check(path)
