from __future__ import annotations

import importlib.machinery
import os
import re
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


WHEEL_TAG_REGEX = "[cp]p[23]_?\\d+-(?:cp[23]_?\\d+m?u?|pypy[23]_?\\d+_pp\\d+)-.+"


shared_lib_extensions = importlib.machinery.EXTENSION_SUFFIXES


@pytest.fixture(autouse=True)
def setup() -> Iterator[None]:
    clear_samples_dist()
    clear_samples_build()

    yield

    clear_samples_dist()
    clear_samples_build()


def clear_samples_dist() -> None:
    for dist in fixtures_dir.glob("**/dist"):
        if dist.is_dir():
            shutil.rmtree(str(dist))


def clear_samples_build() -> None:
    for build in fixtures_dir.glob("**/build"):
        if build.is_dir():
            shutil.rmtree(str(build))
    for suffix in shared_lib_extensions:
        for shared_lib in fixtures_dir.glob(f"**/*{suffix}"):
            shared_lib.unlink()


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


def test_wheel_epoch() -> None:
    module_path = fixtures_dir / "epoch"
    WheelBuilder.make(Factory().create_poetry(module_path))

    whl = module_path / "dist" / "epoch-1!2.0-py2.py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "epoch-1!2.0.dist-info/METADATA" in z.namelist()


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


def test_wheel_build_script_creates_package() -> None:
    module_path = fixtures_dir / "build_script_creates_package"
    WheelBuilder.make(Factory().create_poetry(module_path))

    # Currently, if a  build.py script is used,
    # poetry just assumes the most specific tags
    whl = next((module_path / "dist").glob("my_package-0.1-*.whl"))

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "my_package/__init__.py" in z.namelist()
        assert "my_package/foo.py" in z.namelist()

    shutil.rmtree(module_path / "my_package")


def test_dist_info_file_permissions() -> None:
    module_path = fixtures_dir / "complete"
    WheelBuilder.make(Factory().create_poetry(module_path))

    whl = module_path / "dist" / "my_package-1.2.3-py3-none-any.whl"

    with zipfile.ZipFile(str(whl)) as z:
        assert (
            z.getinfo("my_package-1.2.3.dist-info/WHEEL").external_attr & 0x1FF0000
            == 0o644 << 16
        )
        assert (
            z.getinfo("my_package-1.2.3.dist-info/METADATA").external_attr & 0x1FF0000
            == 0o644 << 16
        )
        assert (
            z.getinfo("my_package-1.2.3.dist-info/RECORD").external_attr & 0x1FF0000
            == 0o644 << 16
        )
        assert (
            z.getinfo("my_package-1.2.3.dist-info/entry_points.txt").external_attr
            & 0x1FF0000
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
    class MockGit:
        def get_ignored_files(self, folder: Path | None = None) -> list[str]:
            # Patch git module to return specific excluded files
            return [
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

    p = mocker.patch("poetry.core.vcs.get_vcs")
    p.return_value = MockGit()
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


@pytest.mark.parametrize("in_venv_build", [True, False])
def test_tag(in_venv_build: bool, mocker: MockerFixture) -> None:
    """Tests that tag returns a valid tag if a build script is used,
    no matter if poetry-core lives inside the build environment or not.
    """
    root = fixtures_dir / "extended"
    builder = WheelBuilder(Factory().create_poetry(root))

    get_sys_tags_spy = mocker.spy(builder, "_get_sys_tags")
    if not in_venv_build:
        mocker.patch("sys.executable", "other/python")

    assert re.match(f"^{WHEEL_TAG_REGEX}$", builder.tag)
    if in_venv_build:
        get_sys_tags_spy.assert_not_called()
    else:
        get_sys_tags_spy.assert_called()


def test_extended_editable_wheel_build() -> None:
    """Tests that an editable wheel made from a project with extensions includes
    the .pth, but does not include the built package itself.
    """
    root = fixtures_dir / "extended"
    WheelBuilder.make_in(Factory().create_poetry(root), editable=True)

    whl = next((root / "dist").glob("extended-0.1-*.whl"))

    assert whl.exists()
    with zipfile.ZipFile(str(whl)) as z:
        assert "extended.pth" in z.namelist()
        # Ensure the directory "extended/" does not exist in the whl
        assert all(not n.startswith("extended/") for n in z.namelist())


def test_extended_editable_build_inplace() -> None:
    """Tests that a project with extensions builds the extension modules in-place
    when ran for an editable install.
    """
    root = fixtures_dir / "extended"
    WheelBuilder.make_in(Factory().create_poetry(root), editable=True)

    # Check that an extension with any of the allowed extensions was built in-place
    assert any(
        (root / "extended" / f"extended{ext}").exists() for ext in shared_lib_extensions
    )


def test_build_py_only_included() -> None:
    """Tests that a build.py that only defined the command build_py (which generates a
    lib folder) will have its artifacts included.
    """
    root = fixtures_dir / "build_with_build_py_only"
    WheelBuilder.make(Factory().create_poetry(root))

    whl = next((root / "dist").glob("build_with_build_py_only-0.1-*.whl"))

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "build_with_build_py_only/generated/file.py" in z.namelist()
