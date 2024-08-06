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
from poetry.core.masonry.builders.sdist import SdistBuilder
from poetry.core.masonry.builders.wheel import WheelBuilder
from tests.masonry.builders.test_wheel import WHEEL_TAG_REGEX


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
    platform.python_implementation().lower() == "pypy", reason="Disable test for PyPy"
)
@pytest.mark.parametrize(
    ["project", "exptected_c_dir"],
    [
        ("extended", "extended"),
        ("extended_with_no_setup", "extended"),
        ("src_extended", "src/extended"),
    ],
)
def test_wheel_c_extension(project: str, exptected_c_dir: str) -> None:
    module_path = fixtures_dir / project
    poetry = Factory().create_poetry(module_path)
    SdistBuilder(poetry).build()
    WheelBuilder(poetry).build()

    sdist = fixtures_dir / project / "dist" / "extended-0.1.tar.gz"
    assert sdist.exists()

    with tarfile.open(sdist, "r") as tar:
        assert "extended-0.1/build.py" in tar.getnames()
        assert f"extended-0.1/{exptected_c_dir}/extended.c" in tar.getnames()

    whl = next(iter((module_path / "dist").glob("extended-0.1-cp*-cp*-*.whl")))
    assert whl.exists()

    with zipfile.ZipFile(whl) as zipf:
        has_compiled_extension = False
        for name in zipf.namelist():
            if name.startswith("extended/extended") and name.endswith((".so", ".pyd")):
                has_compiled_extension = True
        assert has_compiled_extension

        wheel_data = zipf.read("extended-0.1.dist-info/WHEEL").decode()
        assert (
            re.match(
                f"""(?m)^\
Wheel-Version: 1.0
Generator: poetry-core {__version__}
Root-Is-Purelib: false
Tag: {WHEEL_TAG_REGEX}
$""",
                wheel_data,
            )
            is not None
        )

        record = zipf.read("extended-0.1.dist-info/RECORD").decode()
        records = csv.reader(record.splitlines())
        record_files = [row[0] for row in records]
        assert re.search(r"\s+extended/extended.*\.(so|pyd)", record) is not None

        # Files in RECORD should match files in wheel.
        assert zipf.namelist() == record_files
        assert len(set(record_files)) == len(record_files)


@pytest.mark.parametrize("no_vcs", [False, True])
def test_complete(no_vcs: bool) -> None:
    module_path = fixtures_dir / "complete"

    if no_vcs:
        # Copy the complete fixtures dir to a temporary directory
        temporary_dir = Path(tempfile.mkdtemp()) / "complete"
        shutil.copytree(module_path.as_posix(), temporary_dir.as_posix())
        module_path = temporary_dir

    poetry = Factory().create_poetry(module_path)
    with pytest.warns(DeprecationWarning, match=".* script .* extra"):
        SdistBuilder(poetry).build()
        WheelBuilder(poetry).build()

    whl = module_path / "dist" / "my_package-1.2.3-py3-none-any.whl"

    assert whl.exists()
    if sys.platform != "win32":
        assert (os.stat(str(whl)).st_mode & 0o777) == 0o644

    expected_name_list = [
        "my_package/__init__.py",
        "my_package/data1/test.json",
        "my_package/sub_pkg1/__init__.py",
        "my_package/sub_pkg2/__init__.py",
        "my_package/sub_pkg2/data2/data.json",
        "my_package/sub_pkg3/foo.py",
        "my_package-1.2.3.data/scripts/script.sh",
        *sorted(
            [
                "my_package-1.2.3.dist-info/entry_points.txt",
                "my_package-1.2.3.dist-info/LICENSE",
                "my_package-1.2.3.dist-info/METADATA",
                "my_package-1.2.3.dist-info/WHEEL",
                "my_package-1.2.3.dist-info/COPYING",
                "my_package-1.2.3.dist-info/LICENCE",
                "my_package-1.2.3.dist-info/AUTHORS",
            ],
            key=lambda x: Path(x),
        ),
        "my_package-1.2.3.dist-info/RECORD",
    ]

    with zipfile.ZipFile(str(whl)) as zipf:
        assert zipf.namelist() == expected_name_list
        assert (
            "Hello World"
            in zipf.read("my_package-1.2.3.data/scripts/script.sh").decode()
        )

        entry_points = zipf.read("my_package-1.2.3.dist-info/entry_points.txt")

        assert (
            entry_points.decode()
            == """\
[console_scripts]
extra-script=my_package.extra:main[time]
my-2nd-script=my_package:main2
my-script=my_package:main

"""
        )
        wheel_data = zipf.read("my_package-1.2.3.dist-info/WHEEL").decode()

        assert (
            wheel_data
            == f"""\
Wheel-Version: 1.0
Generator: poetry-core {__version__}
Root-Is-Purelib: true
Tag: py3-none-any
"""
        )
        wheel_data = zipf.read("my_package-1.2.3.dist-info/METADATA").decode()

        assert (
            wheel_data
            == """\
Metadata-Version: 2.3
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
Classifier: Programming Language :: Python :: 3.12
Classifier: Programming Language :: Python :: 3.13
Classifier: Topic :: Software Development :: Build Tools
Classifier: Topic :: Software Development :: Libraries :: Python Modules
Provides-Extra: time
Requires-Dist: cachy[msgpack] (>=0.2.0,<0.3.0)
Requires-Dist: cleo (>=0.6,<0.7)
Requires-Dist: pendulum (>=1.4,<2.0) ; (python_version ~= "2.7"\
 and sys_platform == "win32" or python_version in "3.4 3.5") and (extra == "time")
Project-URL: Documentation, https://python-poetry.org/docs
Project-URL: Issue Tracker, https://github.com/python-poetry/poetry/issues
Project-URL: Repository, https://github.com/python-poetry/poetry
Description-Content-Type: text/x-rst

My Package
==========

"""
        )
        actual_records = zipf.read("my_package-1.2.3.dist-info/RECORD").decode()

        # The SHA hashes vary per operating systems.
        # So instead of 1:1 assertion, let's do a bit clunkier one:
        actual_files = [row[0] for row in csv.reader(actual_records.splitlines())]

        assert actual_files == expected_name_list


def test_module_src() -> None:
    module_path = fixtures_dir / "source_file"
    poetry = Factory().create_poetry(module_path)
    SdistBuilder(poetry).build()
    WheelBuilder(poetry).build()

    sdist = module_path / "dist" / "module_src-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "module_src-0.1/src/module_src.py" in tar.getnames()

    whl = module_path / "dist" / "module_src-0.1-py2.py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as zipf:
        assert "module_src.py" in zipf.namelist()


def test_package_src() -> None:
    module_path = fixtures_dir / "source_package"
    poetry = Factory().create_poetry(module_path)
    SdistBuilder(poetry).build()
    WheelBuilder(poetry).build()

    sdist = module_path / "dist" / "package_src-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "package_src-0.1/src/package_src/module.py" in tar.getnames()

    whl = module_path / "dist" / "package_src-0.1-py2.py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as zipf:
        assert "package_src/__init__.py" in zipf.namelist()
        assert "package_src/module.py" in zipf.namelist()


def test_split_source() -> None:
    module_path = fixtures_dir / "split_source"
    poetry = Factory().create_poetry(module_path)
    SdistBuilder(poetry).build()
    WheelBuilder(poetry).build()

    sdist = module_path / "dist" / "split_source-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "split_source-0.1/lib_a/module_a/__init__.py" in tar.getnames()
        assert "split_source-0.1/lib_b/module_b/__init__.py" in tar.getnames()

    whl = module_path / "dist" / "split_source-0.1-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as zipf:
        assert "module_a/__init__.py" in zipf.namelist()
        assert "module_b/__init__.py" in zipf.namelist()


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

    poetry = Factory().create_poetry(module_path)
    SdistBuilder(poetry).build()
    WheelBuilder(poetry).build()

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
        assert "with_include-1.2.3/etc/from_to/__init__.py" in names

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
        assert "target_from_to/from_to/__init__.py" in names
        assert "target_module/my_module_to.py" in names


def test_respect_format_for_explicit_included_files() -> None:
    module_path = fixtures_dir / "exclude-whl-include-sdist"
    poetry = Factory().create_poetry(module_path)
    SdistBuilder(poetry).build()
    WheelBuilder(poetry).build()

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
