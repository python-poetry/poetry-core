from __future__ import annotations

import os
import shutil
import zipfile

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Iterator
from typing import TextIO

import pytest

from poetry.core.factory import Factory
from poetry.core.masonry.builders.wheel import WheelBuilder
from tests.masonry.builders.test_sdist import project


if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch
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


def test_wheel_module() -> None:
    module_path = fixtures_dir / "module1"
    WheelBuilder.make(Factory().create_poetry(module_path))

    whl = module_path / "dist" / "module1-0.1-py2.py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "module1.py" in z.namelist()


def test_wheel_package() -> None:
    module_path = fixtures_dir / "complete"
    WheelBuilder.make(Factory().create_poetry(module_path))

    whl = module_path / "dist" / "my_package-1.2.3-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "my_package/sub_pkg1/__init__.py" in z.namelist()


def test_wheel_prerelease() -> None:
    module_path = fixtures_dir / "prerelease"
    WheelBuilder.make(Factory().create_poetry(module_path))

    whl = module_path / "dist" / "prerelease-0.1b1-py2.py3-none-any.whl"

    assert whl.exists()


def test_wheel_excluded_data() -> None:
    module_path = fixtures_dir / "default_with_excluded_data_toml"
    WheelBuilder.make(Factory().create_poetry(module_path))

    whl = module_path / "dist" / "my_package-1.2.3-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "my_package/__init__.py" in z.namelist()
        assert "my_package/data/sub_data/data2.txt" in z.namelist()
        assert "my_package/data/sub_data/data3.txt" in z.namelist()
        assert "my_package/data/data1.txt" not in z.namelist()


def test_wheel_excluded_nested_data() -> None:
    module_path = fixtures_dir / "exclude_nested_data_toml"
    poetry = Factory().create_poetry(module_path)
    WheelBuilder.make(poetry)

    whl = module_path / "dist" / "my_package-1.2.3-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "my_package/__init__.py" in z.namelist()
        assert "my_package/data/sub_data/data2.txt" not in z.namelist()
        assert "my_package/data/sub_data/data3.txt" not in z.namelist()
        assert "my_package/data/data1.txt" not in z.namelist()
        assert "my_package/data/data2.txt" in z.namelist()
        assert "my_package/puplic/publicdata.txt" in z.namelist()
        assert "my_package/public/item1/itemdata1.txt" not in z.namelist()
        assert "my_package/public/item1/subitem/subitemdata.txt" not in z.namelist()
        assert "my_package/public/item2/itemdata2.txt" not in z.namelist()


def test_include_excluded_code() -> None:
    module_path = fixtures_dir / "include_excluded_code"
    poetry = Factory().create_poetry(module_path)
    wb = WheelBuilder(poetry)
    wb.build()
    whl = module_path / "dist" / wb.wheel_filename
    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "my_package/__init__.py" in z.namelist()
        assert "my_package/generated.py" in z.namelist()
        assert "lib/my_package/generated.py" not in z.namelist()


def test_wheel_localversionlabel() -> None:
    module_path = fixtures_dir / "localversionlabel"
    project = Factory().create_poetry(module_path)
    WheelBuilder.make(project)
    local_version_string = "localversionlabel-0.1b1+gitbranch.buildno.1"
    whl = module_path / "dist" / (local_version_string + "-py2.py3-none-any.whl")

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert local_version_string + ".dist-info/METADATA" in z.namelist()


def test_wheel_package_src() -> None:
    module_path = fixtures_dir / "source_package"
    WheelBuilder.make(Factory().create_poetry(module_path))

    whl = module_path / "dist" / "package_src-0.1-py2.py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "package_src/__init__.py" in z.namelist()
        assert "package_src/module.py" in z.namelist()


def test_wheel_module_src() -> None:
    module_path = fixtures_dir / "source_file"
    WheelBuilder.make(Factory().create_poetry(module_path))

    whl = module_path / "dist" / "module_src-0.1-py2.py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "module_src.py" in z.namelist()


def test_dist_info_file_permissions() -> None:
    module_path = fixtures_dir / "complete"
    WheelBuilder.make(Factory().create_poetry(module_path))

    whl = module_path / "dist" / "my_package-1.2.3-py3-none-any.whl"

    with zipfile.ZipFile(str(whl)) as z:
        assert (
            z.getinfo("my_package-1.2.3.dist-info/WHEEL").external_attr == 0o644 << 16
        )
        assert (
            z.getinfo("my_package-1.2.3.dist-info/METADATA").external_attr
            == 0o644 << 16
        )
        assert (
            z.getinfo("my_package-1.2.3.dist-info/RECORD").external_attr == 0o644 << 16
        )
        assert (
            z.getinfo("my_package-1.2.3.dist-info/entry_points.txt").external_attr
            == 0o644 << 16
        )


def test_wheel_includes_inline_table() -> None:
    module_path = fixtures_dir / "with_include_inline_table"
    WheelBuilder.make(Factory().create_poetry(module_path))

    whl = module_path / "dist" / "with_include-1.2.3-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "both.txt" in z.namelist()
        assert "wheel_only.txt" in z.namelist()
        assert "notes.txt" not in z.namelist()


@pytest.mark.parametrize(
    "package",
    ["pep_561_stub_only", "pep_561_stub_only_partial", "pep_561_stub_only_src"],
)
def test_wheel_package_pep_561_stub_only(package: str) -> None:
    root = fixtures_dir / package
    WheelBuilder.make(Factory().create_poetry(root))

    whl = root / "dist" / "pep_561_stubs-0.1-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "pkg-stubs/__init__.pyi" in z.namelist()
        assert "pkg-stubs/module.pyi" in z.namelist()
        assert "pkg-stubs/subpkg/__init__.pyi" in z.namelist()


def test_wheel_package_pep_561_stub_only_partial_namespace() -> None:
    root = fixtures_dir / "pep_561_stub_only_partial_namespace"
    WheelBuilder.make(Factory().create_poetry(root))

    whl = root / "dist" / "pep_561_stubs-0.1-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "pkg-stubs/module.pyi" in z.namelist()
        assert "pkg-stubs/subpkg/__init__.pyi" in z.namelist()
        assert "pkg-stubs/subpkg/py.typed" in z.namelist()


def test_wheel_package_pep_561_stub_only_includes_typed_marker() -> None:
    root = fixtures_dir / "pep_561_stub_only_partial"
    WheelBuilder.make(Factory().create_poetry(root))

    whl = root / "dist" / "pep_561_stubs-0.1-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "pkg-stubs/py.typed" in z.namelist()


def test_wheel_includes_licenses_in_correct_paths() -> None:
    root = fixtures_dir / "licenses_and_copying"
    WheelBuilder.make(Factory().create_poetry(root))

    whl = root / "dist" / "my_package-1.2.3-py3-none-any.whl"

    assert whl.exists()
    with zipfile.ZipFile(str(whl)) as z:
        assert "my_package-1.2.3.dist-info/COPYING" in z.namelist()
        assert "my_package-1.2.3.dist-info/COPYING.txt" in z.namelist()
        assert "my_package-1.2.3.dist-info/LICENSE" in z.namelist()
        assert "my_package-1.2.3.dist-info/LICENSE.md" in z.namelist()
        assert "my_package-1.2.3.dist-info/LICENSES/CUSTOM-LICENSE" in z.namelist()
        assert "my_package-1.2.3.dist-info/LICENSES/BSD-3.md" in z.namelist()
        assert "my_package-1.2.3.dist-info/LICENSES/MIT.txt" in z.namelist()


def test_wheel_with_file_with_comma() -> None:
    root = fixtures_dir / "comma_file"
    WheelBuilder.make(Factory().create_poetry(root))

    whl = root / "dist" / "comma_file-1.2.3-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        records = z.read("comma_file-1.2.3.dist-info/RECORD")
        assert '\n"comma_file/a,b.py"' in records.decode()


def test_default_src_with_excluded_data(mocker: MockerFixture) -> None:
    # Patch git module to return specific excluded files
    p = mocker.patch("poetry.core.vcs.git.Git.get_ignored_files")
    p.return_value = [
        (
            (
                Path(__file__).parent
                / "fixtures"
                / "default_src_with_excluded_data"
                / "src"
                / "my_package"
                / "data"
                / "sub_data"
                / "data2.txt"
            )
            .relative_to(project("default_src_with_excluded_data"))
            .as_posix()
        )
    ]
    poetry = Factory().create_poetry(project("default_src_with_excluded_data"))

    builder = WheelBuilder(poetry)
    builder.build()

    whl = (
        fixtures_dir
        / "default_src_with_excluded_data"
        / "dist"
        / "my_package-1.2.3-py3-none-any.whl"
    )

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        names = z.namelist()
        assert "my_package/__init__.py" in names
        assert "my_package/data/data1.txt" in names
        assert "my_package/data/sub_data/data2.txt" not in names
        assert "my_package/data/sub_data/data3.txt" in names


def test_wheel_file_is_closed(monkeypatch: MonkeyPatch) -> None:
    """Confirm that wheel zip files are explicitly closed."""

    # Using a list is a hack for Python 2.7 compatibility.
    fd_file: list[TextIO | None] = [None]

    real_fdopen = os.fdopen

    def capturing_fdopen(*args: Any, **kwargs: Any) -> TextIO | None:
        fd_file[0] = real_fdopen(*args, **kwargs)
        return fd_file[0]

    monkeypatch.setattr(os, "fdopen", capturing_fdopen)

    module_path = fixtures_dir / "module1"
    WheelBuilder.make(Factory().create_poetry(module_path))

    assert fd_file[0] is not None
    assert fd_file[0].closed
