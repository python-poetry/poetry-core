from __future__ import annotations

import os
import platform
import sys
import zipfile

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pytest

from poetry.core import __version__
from poetry.core.masonry import api
from poetry.core.utils.helpers import temporary_directory
from tests.testutils import validate_sdist_contents
from tests.testutils import validate_wheel_contents


@contextmanager
def cwd(directory: str | Path) -> Iterator[None]:
    prev = os.getcwd()
    os.chdir(str(directory))
    try:
        yield
    finally:
        os.chdir(prev)


fixtures = os.path.join(os.path.dirname(__file__), "builders", "fixtures")


def test_get_requires_for_build_wheel() -> None:
    expected: list[str] = []
    with cwd(os.path.join(fixtures, "complete")):
        assert api.get_requires_for_build_wheel() == expected


def test_get_requires_for_build_sdist() -> None:
    expected: list[str] = []
    with cwd(os.path.join(fixtures, "complete")):
        assert api.get_requires_for_build_sdist() == expected


def test_build_wheel() -> None:
    with temporary_directory() as tmp_dir, cwd(os.path.join(fixtures, "complete")):
        filename = api.build_wheel(tmp_dir)
        validate_wheel_contents(
            name="my_package",
            version="1.2.3",
            path=str(os.path.join(tmp_dir, filename)),
            files=["entry_points.txt"],
        )


def test_build_wheel_with_include() -> None:
    with temporary_directory() as tmp_dir, cwd(os.path.join(fixtures, "with-include")):
        filename = api.build_wheel(tmp_dir)
        validate_wheel_contents(
            name="with_include",
            version="1.2.3",
            path=str(os.path.join(tmp_dir, filename)),
            files=["entry_points.txt"],
        )


def test_build_wheel_with_bad_path_dev_dep_succeeds() -> None:
    with temporary_directory() as tmp_dir, cwd(
        os.path.join(fixtures, "with_bad_path_dev_dep")
    ):
        api.build_wheel(tmp_dir)


def test_build_wheel_with_bad_path_dep_fails() -> None:
    with pytest.raises(ValueError) as err, temporary_directory() as tmp_dir, cwd(
        os.path.join(fixtures, "with_bad_path_dep")
    ):
        api.build_wheel(tmp_dir)
    assert "does not exist" in str(err.value)


@pytest.mark.skipif(
    sys.platform == "win32"
    and sys.version_info <= (3, 6)
    or platform.python_implementation().lower() == "pypy",
    reason="Disable test on Windows for Python <=3.6 and for PyPy",
)
def test_build_wheel_extended() -> None:
    with temporary_directory() as tmp_dir, cwd(os.path.join(fixtures, "extended")):
        filename = api.build_wheel(tmp_dir)
        whl = Path(tmp_dir) / filename
        assert whl.exists()
        validate_wheel_contents(name="extended", version="0.1", path=whl.as_posix())


def test_build_sdist() -> None:
    with temporary_directory() as tmp_dir, cwd(os.path.join(fixtures, "complete")):
        filename = api.build_sdist(tmp_dir)
        validate_sdist_contents(
            name="my-package",
            version="1.2.3",
            path=str(os.path.join(tmp_dir, filename)),
            files=["LICENSE"],
        )


def test_build_sdist_with_include() -> None:
    with temporary_directory() as tmp_dir, cwd(os.path.join(fixtures, "with-include")):
        filename = api.build_sdist(tmp_dir)
        validate_sdist_contents(
            name="with-include",
            version="1.2.3",
            path=str(os.path.join(tmp_dir, filename)),
            files=["LICENSE"],
        )


def test_build_sdist_with_bad_path_dev_dep_succeeds() -> None:
    with temporary_directory() as tmp_dir, cwd(
        os.path.join(fixtures, "with_bad_path_dev_dep")
    ):
        api.build_sdist(tmp_dir)


def test_build_sdist_with_bad_path_dep_fails() -> None:
    with pytest.raises(ValueError) as err, temporary_directory() as tmp_dir, cwd(
        os.path.join(fixtures, "with_bad_path_dep")
    ):
        api.build_sdist(tmp_dir)
    assert "does not exist" in str(err.value)


def test_prepare_metadata_for_build_wheel() -> None:
    entry_points = """\
[console_scripts]
extra-script=my_package.extra:main[time]
my-2nd-script=my_package:main2
my-script=my_package:main

"""
    wheel_data = f"""\
Wheel-Version: 1.0
Generator: poetry-core {__version__}
Root-Is-Purelib: true
Tag: py3-none-any
"""
    metadata = """\
Metadata-Version: 2.1
Name: my-package
Version: 1.2.3
Summary: Some description.
Home-page: https://python-poetry.org/
License: MIT
Keywords: packaging,dependency,poetry
Author: Sébastien Eustace
Author-email: sebastien@eustace.io
Maintainer: People Everywhere
Maintainer-email: people@everywhere.com
Requires-Python: >=3.6,<4.0
Classifier: License :: OSI Approved :: MIT License
Classifier: Programming Language :: Python :: 3
Classifier: Programming Language :: Python :: 3.6
Classifier: Programming Language :: Python :: 3.7
Classifier: Programming Language :: Python :: 3.8
Classifier: Programming Language :: Python :: 3.9
Classifier: Programming Language :: Python :: 3.10
Classifier: Topic :: Software Development :: Build Tools
Classifier: Topic :: Software Development :: Libraries :: Python Modules
Provides-Extra: time
Requires-Dist: cachy[msgpack] (>=0.2.0,<0.3.0)
Requires-Dist: cleo (>=0.6,<0.7)
Requires-Dist: pendulum (>=1.4,<2.0); (python_version ~= "2.7" and sys_platform == "win32" or python_version in "3.4 3.5") and (extra == "time")
Project-URL: Documentation, https://python-poetry.org/docs
Project-URL: Issue Tracker, https://github.com/python-poetry/poetry/issues
Project-URL: Repository, https://github.com/python-poetry/poetry
Description-Content-Type: text/x-rst

My Package
==========

"""
    with temporary_directory() as tmp_dir, cwd(os.path.join(fixtures, "complete")):
        dirname = api.prepare_metadata_for_build_wheel(tmp_dir)

        assert dirname == "my_package-1.2.3.dist-info"

        dist_info = Path(tmp_dir, dirname)

        assert (dist_info / "entry_points.txt").exists()
        assert (dist_info / "WHEEL").exists()
        assert (dist_info / "METADATA").exists()

        with (dist_info / "entry_points.txt").open(encoding="utf-8") as f:
            assert entry_points == f.read()

        with (dist_info / "WHEEL").open(encoding="utf-8") as f:
            assert wheel_data == f.read()

        with (dist_info / "METADATA").open(encoding="utf-8") as f:
            assert metadata == f.read()


def test_prepare_metadata_for_build_wheel_with_bad_path_dev_dep_succeeds() -> None:
    with temporary_directory() as tmp_dir, cwd(
        os.path.join(fixtures, "with_bad_path_dev_dep")
    ):
        api.prepare_metadata_for_build_wheel(tmp_dir)


def test_prepare_metadata_for_build_wheel_with_bad_path_dep_succeeds() -> None:
    with pytest.raises(ValueError) as err, temporary_directory() as tmp_dir, cwd(
        os.path.join(fixtures, "with_bad_path_dep")
    ):
        api.prepare_metadata_for_build_wheel(tmp_dir)
    assert "does not exist" in str(err.value)


def test_build_editable_wheel() -> None:
    pkg_dir = Path(fixtures) / "complete"

    with temporary_directory() as tmp_dir, cwd(pkg_dir):
        filename = api.build_editable(tmp_dir)
        wheel_pth = Path(tmp_dir) / filename

        validate_wheel_contents(
            name="my_package",
            version="1.2.3",
            path=str(wheel_pth),
        )

        with zipfile.ZipFile(wheel_pth) as z:
            namelist = z.namelist()

            assert "my_package.pth" in namelist
            assert pkg_dir.as_posix() == z.read("my_package.pth").decode().strip()
