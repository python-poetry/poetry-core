from __future__ import annotations

import sys
import tempfile

from pathlib import Path
from stat import S_IREAD
from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from pytest_mock import MockerFixture

from poetry.core.utils.helpers import combine_unicode
from poetry.core.utils.helpers import parse_requires
from poetry.core.utils.helpers import readme_content_type
from poetry.core.utils.helpers import robust_rmtree
from poetry.core.utils.helpers import temporary_directory


def test_parse_requires() -> None:
    requires = """\
jsonschema>=2.6.0.0,<3.0.0.0
lockfile>=0.12.0.0,<0.13.0.0
pip-tools>=1.11.0.0,<2.0.0.0
pkginfo>=1.4.0.0,<2.0.0.0
pyrsistent>=0.14.2.0,<0.15.0.0
toml>=0.9.0.0,<0.10.0.0
cleo>=0.6.0.0,<0.7.0.0
cachy>=0.1.1.0,<0.2.0.0
cachecontrol>=0.12.4.0,<0.13.0.0
requests>=2.18.0.0,<3.0.0.0
msgpack-python>=0.5.0.0,<0.6.0.0
pyparsing>=2.2.0.0,<3.0.0.0
requests-toolbelt>=0.8.0.0,<0.9.0.0

[:(python_version >= "2.7.0.0" and python_version < "2.8.0.0") or (python_version >= "3.4.0.0" and python_version < "3.5.0.0")]
typing>=3.6.0.0,<4.0.0.0

[:python_version >= "2.7.0.0" and python_version < "2.8.0.0"]
virtualenv>=15.2.0.0,<16.0.0.0
pathlib2>=2.3.0.0,<3.0.0.0

[:python_version >= "3.4.0.0" and python_version < "3.6.0.0"]
zipfile36>=0.1.0.0,<0.2.0.0

[dev]
isort@ git+git://github.com/timothycrosley/isort.git@e63ae06ec7d70b06df9e528357650281a3d3ec22#egg=isort
"""
    result = parse_requires(requires)
    expected = [
        "jsonschema>=2.6.0.0,<3.0.0.0",
        "lockfile>=0.12.0.0,<0.13.0.0",
        "pip-tools>=1.11.0.0,<2.0.0.0",
        "pkginfo>=1.4.0.0,<2.0.0.0",
        "pyrsistent>=0.14.2.0,<0.15.0.0",
        "toml>=0.9.0.0,<0.10.0.0",
        "cleo>=0.6.0.0,<0.7.0.0",
        "cachy>=0.1.1.0,<0.2.0.0",
        "cachecontrol>=0.12.4.0,<0.13.0.0",
        "requests>=2.18.0.0,<3.0.0.0",
        "msgpack-python>=0.5.0.0,<0.6.0.0",
        "pyparsing>=2.2.0.0,<3.0.0.0",
        "requests-toolbelt>=0.8.0.0,<0.9.0.0",
        (
            'typing>=3.6.0.0,<4.0.0.0 ; (python_version >= "2.7.0.0" and python_version'
            ' < "2.8.0.0") or (python_version >= "3.4.0.0" and python_version <'
            ' "3.5.0.0")'
        ),
        (
            'virtualenv>=15.2.0.0,<16.0.0.0 ; python_version >= "2.7.0.0" and'
            ' python_version < "2.8.0.0"'
        ),
        (
            'pathlib2>=2.3.0.0,<3.0.0.0 ; python_version >= "2.7.0.0" and'
            ' python_version < "2.8.0.0"'
        ),
        (
            'zipfile36>=0.1.0.0,<0.2.0.0 ; python_version >= "3.4.0.0" and'
            ' python_version < "3.6.0.0"'
        ),
        (
            "isort@"
            " git+git://github.com/timothycrosley/isort.git@e63ae06ec7d70b06df9e528357650281a3d3ec22#egg=isort"
            ' ; extra == "dev"'
        ),
    ]
    assert result == expected


def test_utils_helpers_combine_unicode() -> None:
    combined_expected = "é"
    decomposed = "é"
    assert combined_expected != decomposed

    combined = combine_unicode(decomposed)
    assert combined == combined_expected


def test_utils_helpers_temporary_directory_readonly_file() -> None:
    with temporary_directory() as temp_dir:
        readonly_filename = temp_dir / "file.txt"
        with readonly_filename.open(mode="w+", encoding="utf-8") as readonly_file:
            readonly_file.write("Poetry rocks!")
        readonly_filename.chmod(S_IREAD)

    assert not temp_dir.exists()
    assert not readonly_filename.exists()


@pytest.mark.parametrize(
    "readme, content_type",
    [
        ("README.rst", "text/x-rst"),
        ("README.md", "text/markdown"),
        ("README", "text/plain"),
        (Path("README.rst"), "text/x-rst"),
        (Path("README.md"), "text/markdown"),
        (Path("README"), "text/plain"),
    ],
)
def test_utils_helpers_readme_content_type(
    readme: str | Path, content_type: str
) -> None:
    assert readme_content_type(readme) == content_type


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires Python 3.10 or higher")
def test_temporary_directory_python_3_10_or_newer(mocker: MockerFixture) -> None:
    mocked_rmtree = mocker.patch("shutil.rmtree")
    mocked_temp_dir = mocker.patch("tempfile.TemporaryDirectory")
    mocked_mkdtemp = mocker.patch("tempfile.mkdtemp")

    mocked_temp_dir.return_value.__enter__.return_value = "hello from test"

    with temporary_directory() as tmp:
        assert tmp == Path("hello from test")

    assert not mocked_rmtree.called
    assert not mocked_mkdtemp.called
    mocked_temp_dir.assert_called_with(ignore_cleanup_errors=True)


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires Python 3.10 or higher")
def test_temporary_directory_python_3_10_or_newer_ensure_cleanup_on_error(
    mocker: MockerFixture,
) -> None:
    mocked_rmtree = mocker.patch("shutil.rmtree")
    mocked_temp_dir = mocker.patch("tempfile.TemporaryDirectory")
    mocked_mkdtemp = mocker.patch("tempfile.mkdtemp")

    mocked_temp_dir.return_value.__enter__.return_value = "hello from test"

    with (
        pytest.raises(Exception, match="Something went wrong"),
        temporary_directory() as tmp,
    ):
        assert tmp == Path("hello from test")

        raise Exception("Something went wrong")

    assert not mocked_rmtree.called
    assert not mocked_mkdtemp.called
    mocked_temp_dir.assert_called_with(ignore_cleanup_errors=True)


@pytest.mark.skipif(
    sys.version_info >= (3, 10), reason="Not supported on Python 3.10 or higher"
)
def test_temporary_directory_python_3_9_or_older(mocker: MockerFixture) -> None:
    mocked_rmtree = mocker.patch("shutil.rmtree")
    mocked_temp_dir = mocker.patch("tempfile.TemporaryDirectory")
    mocked_mkdtemp = mocker.patch("tempfile.mkdtemp")

    mocked_mkdtemp.return_value = "hello from test"

    with temporary_directory() as tmp:
        assert tmp == Path("hello from test")

    assert mocked_rmtree.called
    assert mocked_mkdtemp.called
    assert not mocked_temp_dir.called


@pytest.mark.skipif(
    sys.version_info >= (3, 10), reason="Not supported on Python 3.10 or higher"
)
def test_temporary_directory_python_3_9_or_older_ensure_cleanup_on_error(
    mocker: MockerFixture,
) -> None:
    mocked_rmtree = mocker.patch("shutil.rmtree")
    mocked_temp_dir = mocker.patch("tempfile.TemporaryDirectory")
    mocked_mkdtemp = mocker.patch("tempfile.mkdtemp")

    mocked_mkdtemp.return_value = "hello from test"

    with (
        pytest.raises(Exception, match="Something went wrong"),
        temporary_directory() as tmp,
    ):
        assert tmp == Path("hello from test")

        raise Exception("Something went wrong")

    assert mocked_rmtree.called
    assert mocked_mkdtemp.called
    assert not mocked_temp_dir.called


def test_robust_rmtree(mocker: MockerFixture) -> None:
    mocked_rmtree = mocker.patch("shutil.rmtree")

    # this should work after an initial exception
    name = tempfile.mkdtemp()
    mocked_rmtree.side_effect = [
        OSError(
            "Couldn't delete file yet, waiting for references to clear", "mocked path"
        ),
        None,
    ]
    robust_rmtree(name)

    # this should give up after retrying multiple times
    mocked_rmtree.side_effect = OSError(
        "Couldn't delete file yet, this error won't go away after first attempt"
    )
    with pytest.raises(OSError):
        robust_rmtree(name, max_timeout=0.04)

    # clear the side effect (breaks the tear-down otherwise)
    mocker.stop(mocked_rmtree)
    # use the real method to remove the temp folder we created for this test
    robust_rmtree(name)
    assert not Path(name).exists()
