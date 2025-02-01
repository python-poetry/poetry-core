from __future__ import annotations

import os
import zipfile

from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from poetry.core import __version__
from poetry.core.masonry import api
from poetry.core.utils.helpers import temporary_directory
from tests.testutils import validate_sdist_contents
from tests.testutils import validate_wheel_contents


if TYPE_CHECKING:
    from collections.abc import Iterator

    from pytest import LogCaptureFixture


@contextmanager
def cwd(directory: str | Path) -> Iterator[None]:
    prev = Path.cwd()
    os.chdir(str(directory))
    try:
        yield
    finally:
        os.chdir(prev)


fixtures = Path(__file__).parent / "builders" / "fixtures"


@pytest.mark.parametrize("project", ["complete", "complete_new", "complete_dynamic"])
def test_get_requires_for_build_wheel(project: str) -> None:
    expected: list[str] = []
    with cwd(fixtures / project):
        assert api.get_requires_for_build_wheel() == expected


@pytest.mark.parametrize("project", ["complete", "complete_new", "complete_dynamic"])
def test_get_requires_for_build_sdist(project: str) -> None:
    expected: list[str] = []
    with cwd(fixtures / project):
        assert api.get_requires_for_build_sdist() == expected


@pytest.mark.parametrize("project", ["complete", "complete_new", "complete_dynamic"])
def test_build_wheel(project: str) -> None:
    with temporary_directory() as tmp_dir, cwd(fixtures / project):
        filename = api.build_wheel(str(tmp_dir))
        validate_wheel_contents(
            name="my_package",
            version="1.2.3",
            path=tmp_dir / filename,
            files=["entry_points.txt"],
        )


def test_build_wheel_with_local_version() -> None:
    with temporary_directory() as tmp_dir, cwd(fixtures / "complete"):
        filename = api.build_wheel(
            str(tmp_dir), config_settings={"local-version": "some-label"}
        )
        validate_wheel_contents(
            name="my_package",
            version="1.2.3+some-label",
            path=tmp_dir / filename,
            files=["entry_points.txt"],
        )


def test_build_wheel_with_include() -> None:
    with temporary_directory() as tmp_dir, cwd(fixtures / "with-include"):
        filename = api.build_wheel(str(tmp_dir))
        validate_wheel_contents(
            name="with_include",
            version="1.2.3",
            path=tmp_dir / filename,
            files=["entry_points.txt"],
        )


def test_build_wheel_with_bad_path_dev_dep_succeeds() -> None:
    with temporary_directory() as tmp_dir, cwd(fixtures / "with_bad_path_dev_dep"):
        api.build_wheel(str(tmp_dir))


def test_build_wheel_with_bad_path_dep_succeeds(caplog: LogCaptureFixture) -> None:
    with temporary_directory() as tmp_dir, cwd(fixtures / "with_bad_path_dep"):
        api.build_wheel(str(tmp_dir))
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "WARNING"
    assert "does not exist" in record.message


def test_build_wheel_extended() -> None:
    with temporary_directory() as tmp_dir, cwd(fixtures / "extended"):
        filename = api.build_wheel(str(tmp_dir))
        whl = Path(tmp_dir) / filename
        assert whl.exists()
        validate_wheel_contents(name="extended", version="0.1", path=whl)


@pytest.mark.parametrize("project", ["complete", "complete_new", "complete_dynamic"])
def test_build_sdist(project: str) -> None:
    with temporary_directory() as tmp_dir, cwd(fixtures / project):
        filename = api.build_sdist(str(tmp_dir))
        validate_sdist_contents(
            name="my-package",
            version="1.2.3",
            path=tmp_dir / filename,
            files=["LICENSE"],
        )


def test_build_sdist_with_local_version() -> None:
    with temporary_directory() as tmp_dir, cwd(fixtures / "complete"):
        filename = api.build_sdist(
            str(tmp_dir), config_settings={"local-version": "some-label"}
        )
        validate_sdist_contents(
            name="my-package",
            version="1.2.3+some-label",
            path=tmp_dir / filename,
            files=["LICENSE"],
        )


def test_build_sdist_with_include() -> None:
    with temporary_directory() as tmp_dir, cwd(fixtures / "with-include"):
        filename = api.build_sdist(str(tmp_dir))
        validate_sdist_contents(
            name="with-include",
            version="1.2.3",
            path=tmp_dir / filename,
            files=["LICENSE"],
        )


def test_build_sdist_with_bad_path_dev_dep_succeeds() -> None:
    with temporary_directory() as tmp_dir, cwd(fixtures / "with_bad_path_dev_dep"):
        api.build_sdist(str(tmp_dir))


def test_build_sdist_with_bad_path_dep_succeeds(caplog: LogCaptureFixture) -> None:
    with temporary_directory() as tmp_dir, cwd(fixtures / "with_bad_path_dep"):
        api.build_sdist(str(tmp_dir))
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "WARNING"
    assert "does not exist" in record.message


@pytest.mark.parametrize("project", ["complete", "complete_new", "complete_dynamic"])
def test_prepare_metadata_for_build_wheel(project: str) -> None:
    entry_points = """\
[console_scripts]
extra-script=my_package.extra:main
my-2nd-script=my_package:main2
my-script=my_package:main

[poetry.application.plugin]
my-command=my_package.plugins:MyApplicationPlugin

"""
    wheel_data = f"""\
Wheel-Version: 1.0
Generator: poetry-core {__version__}
Root-Is-Purelib: true
Tag: py3-none-any
"""
    metadata = """\
Metadata-Version: 2.3
Name: my-package
Version: 1.2.3
Summary: Some description.
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
Requires-Dist: pendulum (>=1.4,<2.0) ; (python_version ~= "2.7" and sys_platform == "win32" or python_version in "3.4 3.5") and (extra == "time")
Project-URL: Documentation, https://python-poetry.org/docs
Project-URL: Homepage, https://python-poetry.org/
Project-URL: Issue Tracker, https://github.com/python-poetry/poetry/issues
Project-URL: Repository, https://github.com/python-poetry/poetry
Description-Content-Type: text/x-rst

My Package
==========

"""
    with temporary_directory() as tmp_dir, cwd(fixtures / project):
        dirname = api.prepare_metadata_for_build_wheel(str(tmp_dir))

        assert dirname == "my_package-1.2.3.dist-info"

        dist_info = Path(tmp_dir, dirname)

        assert (dist_info / "entry_points.txt").exists()
        assert (dist_info / "WHEEL").exists()
        assert (dist_info / "METADATA").exists()

        with (dist_info / "entry_points.txt").open(encoding="utf-8") as f:
            assert f.read() == entry_points

        with (dist_info / "WHEEL").open(encoding="utf-8") as f:
            assert f.read() == wheel_data

        with (dist_info / "METADATA").open(encoding="utf-8") as f:
            assert f.read() == metadata


def test_prepare_metadata_for_build_wheel_with_local_version() -> None:
    local_version = "some-label"
    entry_points = """\
[console_scripts]
extra-script=my_package.extra:main
my-2nd-script=my_package:main2
my-script=my_package:main

[poetry.application.plugin]
my-command=my_package.plugins:MyApplicationPlugin

"""
    wheel_data = f"""\
Wheel-Version: 1.0
Generator: poetry-core {__version__}
Root-Is-Purelib: true
Tag: py3-none-any
"""
    metadata = f"""\
Metadata-Version: 2.3
Name: my-package
Version: 1.2.3+{local_version}
Summary: Some description.
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
Requires-Dist: pendulum (>=1.4,<2.0) ; (python_version ~= "2.7" and sys_platform == "win32" or python_version in "3.4 3.5") and (extra == "time")
Project-URL: Documentation, https://python-poetry.org/docs
Project-URL: Homepage, https://python-poetry.org/
Project-URL: Issue Tracker, https://github.com/python-poetry/poetry/issues
Project-URL: Repository, https://github.com/python-poetry/poetry
Description-Content-Type: text/x-rst

My Package
==========

"""
    with temporary_directory() as tmp_dir, cwd(fixtures / "complete"):
        dirname = api.prepare_metadata_for_build_wheel(
            str(tmp_dir), config_settings={"local-version": local_version}
        )

        assert dirname == f"my_package-1.2.3+{local_version}.dist-info"

        dist_info = Path(tmp_dir, dirname)

        assert (dist_info / "entry_points.txt").exists()
        assert (dist_info / "WHEEL").exists()
        assert (dist_info / "METADATA").exists()

        with (dist_info / "entry_points.txt").open(encoding="utf-8") as f:
            assert f.read() == entry_points

        with (dist_info / "WHEEL").open(encoding="utf-8") as f:
            assert f.read() == wheel_data

        with (dist_info / "METADATA").open(encoding="utf-8") as f:
            assert f.read() == metadata


def test_prepare_metadata_excludes_optional_without_extras() -> None:
    with (
        temporary_directory() as tmp_dir,
        cwd(fixtures / "with_optional_without_extras"),
    ):
        dirname = api.prepare_metadata_for_build_wheel(str(tmp_dir))
        dist_info = Path(tmp_dir, dirname)
        assert (dist_info / "METADATA").exists()

        with (dist_info / "METADATA").open(encoding="utf-8") as f:
            assert (
                f.read()
                == """\
Metadata-Version: 2.3
Name: my-packager
Version: 0.1
Summary: Something
Classifier: Topic :: Software Development :: Build Tools
Classifier: Topic :: Software Development :: Libraries :: Python Modules
Provides-Extra: grpc
Provides-Extra: http
Requires-Dist: grpcio (>=0.2.0,<0.3.0) ; extra == "grpc"
Requires-Dist: httpx (>=0.28.1,<0.29.0) ; extra == "http"
Requires-Dist: pycowsay (>=0.1.0,<0.2.0)
"""
            )


def test_prepare_metadata_for_build_wheel_with_bad_path_dev_dep_succeeds() -> None:
    with temporary_directory() as tmp_dir, cwd(fixtures / "with_bad_path_dev_dep"):
        api.prepare_metadata_for_build_wheel(str(tmp_dir))


def test_prepare_metadata_for_build_wheel_with_bad_path_dep_succeeds(
    caplog: LogCaptureFixture,
) -> None:
    with temporary_directory() as tmp_dir, cwd(fixtures / "with_bad_path_dep"):
        api.prepare_metadata_for_build_wheel(str(tmp_dir))
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "WARNING"
    assert "does not exist" in record.message


@pytest.mark.parametrize("project", ["complete", "complete_new", "complete_dynamic"])
def test_build_editable_wheel(project: str) -> None:
    pkg_dir = fixtures / project
    with temporary_directory() as tmp_dir, cwd(pkg_dir):
        filename = api.build_editable(str(tmp_dir))
        wheel_pth = Path(tmp_dir) / filename

        validate_wheel_contents(
            name="my_package",
            version="1.2.3",
            path=wheel_pth,
        )

        with zipfile.ZipFile(wheel_pth) as z:
            namelist = z.namelist()

            assert "my_package.pth" in namelist
            assert z.read("my_package.pth").decode().strip() == pkg_dir.as_posix()


def test_build_editable_wheel_with_local_version() -> None:
    pkg_dir = fixtures / "complete"
    with temporary_directory() as tmp_dir, cwd(pkg_dir):
        filename = api.build_editable(
            str(tmp_dir), config_settings={"local-version": "some-label"}
        )
        wheel_pth = Path(tmp_dir) / filename

        validate_wheel_contents(
            name="my_package",
            version="1.2.3+some-label",
            path=wheel_pth,
        )


@pytest.mark.parametrize("project", ["complete", "complete_new", "complete_dynamic"])
def test_build_wheel_with_metadata_directory(project: str) -> None:
    pkg_dir = fixtures / project

    with temporary_directory() as metadata_tmp_dir, cwd(pkg_dir):
        metadata_directory = api.prepare_metadata_for_build_wheel(str(metadata_tmp_dir))

        with temporary_directory() as wheel_tmp_dir:
            dist_info_path = Path(metadata_tmp_dir) / metadata_directory
            (dist_info_path / "CUSTOM").touch()
            filename = api.build_wheel(
                str(wheel_tmp_dir), metadata_directory=str(dist_info_path)
            )
            wheel_pth = Path(wheel_tmp_dir) / filename

            validate_wheel_contents(
                name="my_package",
                version="1.2.3",
                path=wheel_pth,
                files=["entry_points.txt"],
            )

            with zipfile.ZipFile(wheel_pth) as z:
                namelist = z.namelist()

                assert f"{metadata_directory}/CUSTOM" in namelist


@pytest.mark.parametrize("project", ["complete", "complete_new", "complete_dynamic"])
def test_build_editable_wheel_with_metadata_directory(project: str) -> None:
    pkg_dir = fixtures / project

    with temporary_directory() as metadata_tmp_dir, cwd(pkg_dir):
        metadata_directory = api.prepare_metadata_for_build_editable(
            str(metadata_tmp_dir)
        )

        with temporary_directory() as wheel_tmp_dir:
            dist_info_path = Path(metadata_tmp_dir) / metadata_directory
            (dist_info_path / "CUSTOM").touch()
            filename = api.build_editable(
                str(wheel_tmp_dir), metadata_directory=str(dist_info_path)
            )
            wheel_pth = Path(wheel_tmp_dir) / filename

            validate_wheel_contents(
                name="my_package",
                version="1.2.3",
                path=wheel_pth,
                files=["entry_points.txt"],
            )

            with zipfile.ZipFile(wheel_pth) as z:
                namelist = z.namelist()

                assert "my_package.pth" in namelist
                assert z.read("my_package.pth").decode().strip() == pkg_dir.as_posix()
                assert f"{metadata_directory}/CUSTOM" in namelist
