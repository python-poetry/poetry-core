# These test scenarios are ported over from pypa/pip
# https://raw.githubusercontent.com/pypa/pip/b447f438df08303f4f07f2598f190e73876443ba/tests/unit/test_urls.py

import sys

from poetry.core._vendor.six.moves.urllib.request import pathname2url  # noqa

import pytest

from poetry.core.packages import path_to_url
from poetry.core.packages import url_to_path
from poetry.core.utils._compat import Path


@pytest.mark.skipif("sys.platform == 'win32'")
def test_path_to_url_unix():
    assert path_to_url("/tmp/file") == "file:///tmp/file"
    path = Path(".") / "file"
    assert path_to_url("file") == "file://" + path.absolute().as_posix()


@pytest.mark.skipif("sys.platform != 'win32'")
def test_path_to_url_win():
    assert path_to_url("c:/tmp/file") == "file:///c:/tmp/file"
    assert path_to_url("c:\\tmp\\file") == "file:///c:/tmp/file"
    assert path_to_url(r"\\unc\as\path") == "file://unc/as/path"
    path = Path(".") / "file"
    assert path_to_url("file") == "file:///" + path.absolute().as_posix()


@pytest.mark.parametrize(
    "url,win_expected,non_win_expected",
    [
        ("file:tmp", "tmp", "tmp"),
        ("file:c:/path/to/file", r"C:\path\to\file", "c:/path/to/file"),
        ("file:/path/to/file", r"\path\to\file", "/path/to/file"),
        ("file://localhost/tmp/file", r"\tmp\file", "/tmp/file"),
        ("file://localhost/c:/tmp/file", r"C:\tmp\file", "/c:/tmp/file"),
        ("file://somehost/tmp/file", r"\\somehost\tmp\file", None),
        ("file:///tmp/file", r"\tmp\file", "/tmp/file"),
        ("file:///c:/tmp/file", r"C:\tmp\file", "/c:/tmp/file"),
    ],
)
def test_url_to_path(url, win_expected, non_win_expected):
    if sys.platform == "win32":
        expected_path = win_expected
    else:
        expected_path = non_win_expected

    if expected_path is None:
        with pytest.raises(ValueError):
            url_to_path(url)
    else:
        assert url_to_path(url) == Path(expected_path)


@pytest.mark.skipif("sys.platform != 'win32'")
def test_url_to_path_path_to_url_symmetry_win():
    path = r"C:\tmp\file"
    assert url_to_path(path_to_url(path)) == Path(path)

    unc_path = r"\\unc\share\path"
    assert url_to_path(path_to_url(unc_path)) == Path(unc_path)
