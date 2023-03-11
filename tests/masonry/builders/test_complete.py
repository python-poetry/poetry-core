from __future__ import annotations

import csv
import os
import platform
import re
import shutil
import sys
import tarfile
import tempfile
import zipfile

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Iterator

import pytest

from poetry.core import __version__
from poetry.core.factory import Factory
from poetry.core.masonry.builder import Builder


if TYPE_CHECKING:
    from pytest_mock import MockerFixture

fixtures_dir = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def setup() -> Iterator[None]:
    clear_samples_dist()

    yield

    clear_samples_dist()


def clear_samples_dist() -> None:
    for dist in fixtures_dir.glob("**/dist"):
        if dist.is_dir():
            shutil.rmtree(str(dist))


@pytest.mark.skipif(
    sys.platform == "win32"
    and sys.version_info <= (3, 6)
    or platform.python_implementation().lower() == "pypy",
    reason="Disable test on Windows for Python <=3.6 and for PyPy",
)
def test_wheel_c_extension() -> None:  # NOSONAR
    module_path = fixtures_dir / "extended"
    builder = Builder(Factory().create_poetry(module_path))
    builder.build(fmt="all")

    sdist = fixtures_dir / "extended" / "dist" / "extended-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "extended-0.1/build.py" in tar.getnames()
        assert "extended-0.1/extended/extended.c" in tar.getnames()

    whl = list((module_path / "dist").glob("extended-0.1-cp*-cp*-*.whl"))[0]

    assert whl.exists()

    zip = zipfile.ZipFile(str(whl))

    has_compiled_extension = False
    for name in zip.namelist():
        if name.startswith("extended/extended") and name.endswith((".so", ".pyd")):
            has_compiled_extension = True

    assert has_compiled_extension

    try:
        wheel_data = zip.read("extended-0.1.dist-info/WHEEL").decode()

        assert (
            re.match(
                f"""(?m)^\
Wheel-Version: 1.0
Generator: poetry-core {__version__}
Root-Is-Purelib: false
Tag: cp[23]_?\\d+-cp[23]_?\\d+m?u?-.+
$""",
                wheel_data,
            )
            is not None
        )

        record = zip.read("extended-0.1.dist-info/RECORD").decode()
        records = csv.reader(record.splitlines())
        record_files = [row[0] for row in records]

        assert re.search(r"\s+extended/extended.*\.(so|pyd)", record) is not None
    finally:
        zip.close()

    # Files in RECORD should match files in wheel.
    zip_files = sorted(zip.namelist())
    assert zip_files == sorted(record_files)
    assert len(set(record_files)) == len(record_files)


@pytest.mark.skipif(
    sys.platform == "win32"
    and sys.version_info <= (3, 6)
    or platform.python_implementation().lower() == "pypy",
    reason="Disable test on Windows for Python <=3.6 and for PyPy",
)
def test_wheel_c_extension_with_no_setup() -> None:  # NOSONAR
    module_path = fixtures_dir / "extended_with_no_setup"
    builder = Builder(Factory().create_poetry(module_path))
    builder.build(fmt="all")

    sdist = fixtures_dir / "extended_with_no_setup" / "dist" / "extended-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "extended-0.1/build.py" in tar.getnames()
        assert "extended-0.1/extended/extended.c" in tar.getnames()

    whl = list((module_path / "dist").glob("extended-0.1-cp*-cp*-*.whl"))[0]

    assert whl.exists()

    zip = zipfile.ZipFile(str(whl))

    has_compiled_extension = False
    for name in zip.namelist():
        if name.startswith("extended/extended") and name.endswith((".so", ".pyd")):
            has_compiled_extension = True

    assert has_compiled_extension

    try:
        wheel_data = zip.read("extended-0.1.dist-info/WHEEL").decode()

        assert (
            re.match(
                f"""(?m)^\
Wheel-Version: 1.0
Generator: poetry-core {__version__}
Root-Is-Purelib: false
Tag: cp[23]_?\\d+-cp[23]_?\\d+m?u?-.+
$""",
                wheel_data,
            )
            is not None
        )

        record = zip.read("extended-0.1.dist-info/RECORD").decode()
        records = csv.reader(record.splitlines())
        record_files = [row[0] for row in records]

        assert re.search(r"\s+extended/extended.*\.(so|pyd)", record) is not None
    finally:
        zip.close()

    # Files in RECORD should match files in wheel.
    zip_files = sorted(zip.namelist())
    assert zip_files == sorted(record_files)
    assert len(set(record_files)) == len(record_files)


@pytest.mark.skipif(
    sys.platform == "win32"
    and sys.version_info <= (3, 6)
    or platform.python_implementation().lower() == "pypy",
    reason="Disable test on Windows for Python <=3.6 and for PyPy",
)
def test_wheel_c_extension_src_layout() -> None:  # NOSONAR
    module_path = fixtures_dir / "src_extended"
    builder = Builder(Factory().create_poetry(module_path))
    builder.build(fmt="all")

    sdist = fixtures_dir / "src_extended" / "dist" / "extended-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "extended-0.1/build.py" in tar.getnames()
        assert "extended-0.1/src/extended/extended.c" in tar.getnames()

    whl = list((module_path / "dist").glob("extended-0.1-cp*-cp*-*.whl"))[0]

    assert whl.exists()

    zip = zipfile.ZipFile(str(whl))

    has_compiled_extension = False
    for name in zip.namelist():
        if name.startswith("extended/extended") and name.endswith((".so", ".pyd")):
            has_compiled_extension = True

    assert has_compiled_extension

    try:
        wheel_data = zip.read("extended-0.1.dist-info/WHEEL").decode()

        assert (
            re.match(
                f"""(?m)^\
Wheel-Version: 1.0
Generator: poetry-core {__version__}
Root-Is-Purelib: false
Tag: cp[23]_?\\d+-cp[23]_?\\d+m?u?-.+
$""",
                wheel_data,
            )
            is not None
        )

        record = zip.read("extended-0.1.dist-info/RECORD").decode()
        records = csv.reader(record.splitlines())
        record_files = [row[0] for row in records]

        assert re.search(r"\s+extended/extended.*\.(so|pyd)", record) is not None
    finally:
        zip.close()

    # Files in RECORD should match files in wheel.
    zip_files = sorted(zip.namelist())
    assert zip_files == sorted(record_files)
    assert len(set(record_files)) == len(record_files)


def test_complete() -> None:
    module_path = fixtures_dir / "complete"
    builder = Builder(Factory().create_poetry(module_path))
    builder.build(fmt="all")

    whl = module_path / "dist" / "my_package-1.2.3-py3-none-any.whl"

    assert whl.exists()
    if sys.platform != "win32":
        assert (os.stat(str(whl)).st_mode & 0o777) == 0o644

    zip = zipfile.ZipFile(str(whl))

    try:
        assert "my_package/sub_pgk1/extra_file.xml" not in zip.namelist()
        assert "my_package-1.2.3.data/scripts/script.sh" in zip.namelist()
        assert (
            "Hello World"
            in zip.read("my_package-1.2.3.data/scripts/script.sh").decode()
        )

        entry_points = zip.read("my_package-1.2.3.dist-info/entry_points.txt")

        assert (
            entry_points.decode()
            == """\
[console_scripts]
extra-script=my_package.extra:main[time]
my-2nd-script=my_package:main2
my-script=my_package:main

"""
        )
        wheel_data = zip.read("my_package-1.2.3.dist-info/WHEEL").decode()

        assert (
            wheel_data
            == f"""\
Wheel-Version: 1.0
Generator: poetry-core {__version__}
Root-Is-Purelib: true
Tag: py3-none-any
"""
        )
        wheel_data = zip.read("my_package-1.2.3.dist-info/METADATA").decode()

        assert (
            wheel_data
            == """\
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
Classifier: Programming Language :: Python :: 3.11
Classifier: Topic :: Software Development :: Build Tools
Classifier: Topic :: Software Development :: Libraries :: Python Modules
Provides-Extra: time
Requires-Dist: cachy[msgpack] (>=0.2.0,<0.3.0)
Requires-Dist: cleo (>=0.6,<0.7)
Requires-Dist: pendulum (>=1.4,<2.0) ; (python_version ~= "2.7" and sys_platform == "win32" or python_version in "3.4 3.5") and (extra == "time")
Project-URL: Documentation, https://python-poetry.org/docs
Project-URL: Issue Tracker, https://github.com/python-poetry/poetry/issues
Project-URL: Repository, https://github.com/python-poetry/poetry
Description-Content-Type: text/x-rst

My Package
==========

"""
        )
        actual_records = zip.read("my_package-1.2.3.dist-info/RECORD").decode()

        # For some reason, the ordering of the files and the SHA hashes
        # vary per operating systems and Python versions.
        # So instead of 1:1 assertion, let's do a bit clunkier one:

        actual_files = [row[0] for row in csv.reader(actual_records.splitlines())]
        expected_files = [
            "my_package-1.2.3.data/scripts/script.sh",
            "my_package-1.2.3.dist-info/LICENSE",
            "my_package-1.2.3.dist-info/METADATA",
            "my_package-1.2.3.dist-info/RECORD",
            "my_package-1.2.3.dist-info/WHEEL",
            "my_package-1.2.3.dist-info/entry_points.txt",
            "my_package/__init__.py",
            "my_package/data1/test.json",
            "my_package/sub_pkg1/__init__.py",
            "my_package/sub_pkg2/__init__.py",
            "my_package/sub_pkg2/data2/data.json",
            "my_package/sub_pkg3/foo.py",
        ]

        assert sorted(expected_files) == sorted(actual_files)

    finally:
        zip.close()


def test_complete_no_vcs() -> None:
    # Copy the complete fixtures dir to a temporary directory
    module_path = fixtures_dir / "complete"
    temporary_dir = Path(tempfile.mkdtemp()) / "complete"

    shutil.copytree(module_path.as_posix(), temporary_dir.as_posix())

    builder = Builder(Factory().create_poetry(temporary_dir))
    builder.build(fmt="all")

    whl = temporary_dir / "dist" / "my_package-1.2.3-py3-none-any.whl"

    assert whl.exists()

    zip = zipfile.ZipFile(str(whl))

    # Check the zipped file to be sure that included and excluded files are
    # correctly taken account of without vcs
    expected_name_list = [
        "my_package/__init__.py",
        "my_package/data1/test.json",
        "my_package/sub_pkg1/__init__.py",
        "my_package/sub_pkg2/__init__.py",
        "my_package/sub_pkg2/data2/data.json",
        "my_package-1.2.3.data/scripts/script.sh",
        "my_package/sub_pkg3/foo.py",
        "my_package-1.2.3.dist-info/entry_points.txt",
        "my_package-1.2.3.dist-info/LICENSE",
        "my_package-1.2.3.dist-info/WHEEL",
        "my_package-1.2.3.dist-info/METADATA",
        "my_package-1.2.3.dist-info/RECORD",
    ]

    assert sorted(zip.namelist()) == sorted(expected_name_list)

    try:
        entry_points = zip.read("my_package-1.2.3.dist-info/entry_points.txt")

        assert (
            entry_points.decode()
            == """\
[console_scripts]
extra-script=my_package.extra:main[time]
my-2nd-script=my_package:main2
my-script=my_package:main

"""
        )
        wheel_data = zip.read("my_package-1.2.3.dist-info/WHEEL").decode()

        assert (
            wheel_data
            == f"""\
Wheel-Version: 1.0
Generator: poetry-core {__version__}
Root-Is-Purelib: true
Tag: py3-none-any
"""
        )
        wheel_data = zip.read("my_package-1.2.3.dist-info/METADATA").decode()

        assert (
            wheel_data
            == """\
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
Classifier: Programming Language :: Python :: 3.11
Classifier: Topic :: Software Development :: Build Tools
Classifier: Topic :: Software Development :: Libraries :: Python Modules
Provides-Extra: time
Requires-Dist: cachy[msgpack] (>=0.2.0,<0.3.0)
Requires-Dist: cleo (>=0.6,<0.7)
Requires-Dist: pendulum (>=1.4,<2.0) ; (python_version ~= "2.7" and sys_platform == "win32" or python_version in "3.4 3.5") and (extra == "time")
Project-URL: Documentation, https://python-poetry.org/docs
Project-URL: Issue Tracker, https://github.com/python-poetry/poetry/issues
Project-URL: Repository, https://github.com/python-poetry/poetry
Description-Content-Type: text/x-rst

My Package
==========

"""
        )
    finally:
        zip.close()


def test_module_src() -> None:
    module_path = fixtures_dir / "source_file"
    builder = Builder(Factory().create_poetry(module_path))
    builder.build(fmt="all")

    sdist = module_path / "dist" / "module_src-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "module_src-0.1/src/module_src.py" in tar.getnames()

    whl = module_path / "dist" / "module_src-0.1-py2.py3-none-any.whl"

    assert whl.exists()

    zip = zipfile.ZipFile(str(whl))

    try:
        assert "module_src.py" in zip.namelist()
    finally:
        zip.close()


def test_package_src() -> None:
    module_path = fixtures_dir / "source_package"
    builder = Builder(Factory().create_poetry(module_path))
    builder.build(fmt="all")

    sdist = module_path / "dist" / "package_src-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "package_src-0.1/src/package_src/module.py" in tar.getnames()

    whl = module_path / "dist" / "package_src-0.1-py2.py3-none-any.whl"

    assert whl.exists()

    zip = zipfile.ZipFile(str(whl))

    try:
        assert "package_src/__init__.py" in zip.namelist()
        assert "package_src/module.py" in zip.namelist()
    finally:
        zip.close()


def test_split_source() -> None:
    module_path = fixtures_dir / "split_source"
    builder = Builder(Factory().create_poetry(module_path))
    builder.build(fmt="all")

    sdist = module_path / "dist" / "split_source-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "split_source-0.1/lib_a/module_a/__init__.py" in tar.getnames()
        assert "split_source-0.1/lib_b/module_b/__init__.py" in tar.getnames()

    whl = module_path / "dist" / "split_source-0.1-py3-none-any.whl"

    assert whl.exists()

    zip = zipfile.ZipFile(str(whl))

    try:
        assert "module_a/__init__.py" in zip.namelist()
        assert "module_b/__init__.py" in zip.namelist()
    finally:
        zip.close()


def test_package_with_include(mocker: MockerFixture) -> None:
    module_path = fixtures_dir / "with-include"

    # Patch git module to return specific excluded files
    p = mocker.patch("poetry.core.vcs.git.Git.get_ignored_files")
    p.return_value = [
        str(
            Path(__file__).parent
            / "fixtures"
            / "with-include"
            / "extra_dir"
            / "vcs_excluded.txt"
        ),
        str(
            Path(__file__).parent
            / "fixtures"
            / "with-include"
            / "extra_dir"
            / "sub_pkg"
            / "vcs_excluded.txt"
        ),
    ]
    builder = Builder(Factory().create_poetry(module_path))
    builder.build(fmt="all")

    sdist = fixtures_dir / "with-include" / "dist" / "with_include-1.2.3.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        names = tar.getnames()
        assert len(names) == len(set(names))
        assert "with_include-1.2.3/LICENSE" in names
        assert "with_include-1.2.3/README.rst" in names
        assert "with_include-1.2.3/extra_dir/__init__.py" in names
        assert "with_include-1.2.3/extra_dir/vcs_excluded.txt" in names
        assert "with_include-1.2.3/extra_dir/sub_pkg/__init__.py" in names
        assert "with_include-1.2.3/extra_dir/sub_pkg/vcs_excluded.txt" not in names
        assert "with_include-1.2.3/my_module.py" in names
        assert "with_include-1.2.3/notes.txt" in names
        assert "with_include-1.2.3/package_with_include/__init__.py" in names
        assert "with_include-1.2.3/tests/__init__.py" in names
        assert "with_include-1.2.3/pyproject.toml" in names
        assert "with_include-1.2.3/PKG-INFO" in names
        assert "with_include-1.2.3/for_wheel_only/__init__.py" not in names
        assert "with_include-1.2.3/src/src_package/__init__.py" in names

    whl = module_path / "dist" / "with_include-1.2.3-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        names = z.namelist()
        assert len(names) == len(set(names))
        assert "with_include-1.2.3.dist-info/LICENSE" in names
        assert "extra_dir/__init__.py" in names
        assert "extra_dir/vcs_excluded.txt" in names
        assert "extra_dir/sub_pkg/__init__.py" in names
        assert "extra_dir/sub_pkg/vcs_excluded.txt" not in names
        assert "for_wheel_only/__init__.py" in names
        assert "my_module.py" in names
        assert "notes.txt" in names
        assert "package_with_include/__init__.py" in names
        assert "tests/__init__.py" not in names
        assert "src_package/__init__.py" in names


def test_respect_format_for_explicit_included_files() -> None:
    module_path = fixtures_dir / "exclude-whl-include-sdist"
    builder = Builder(Factory().create_poetry(module_path))
    builder.build(fmt="all")

    sdist = module_path / "dist" / "exclude_whl_include_sdist-0.1.0.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        names = tar.getnames()
        assert (
            "exclude_whl_include_sdist-0.1.0/exclude_whl_include_sdist/__init__.py"
            in names
        )
        assert (
            "exclude_whl_include_sdist-0.1.0/exclude_whl_include_sdist/compiled/source.c"
            in names
        )
        assert (
            "exclude_whl_include_sdist-0.1.0/exclude_whl_include_sdist/compiled/source.h"
            in names
        )
        assert (
            "exclude_whl_include_sdist-0.1.0/exclude_whl_include_sdist/cython_code.pyx"
            in names
        )
        assert "exclude_whl_include_sdist-0.1.0/pyproject.toml" in names
        assert "exclude_whl_include_sdist-0.1.0/PKG-INFO" in names

    whl = module_path / "dist" / "exclude_whl_include_sdist-0.1.0-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        names = z.namelist()
        assert "exclude_whl_include_sdist/__init__.py" in names
        assert "exclude_whl_include_sdist/compiled/source.c" not in names
        assert "exclude_whl_include_sdist/compiled/source.h" not in names
        assert "exclude_whl_include_sdist/cython_code.pyx" not in names
