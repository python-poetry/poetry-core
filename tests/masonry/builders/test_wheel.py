from __future__ import annotations

import importlib.machinery
import os
import re
import zipfile

from typing import TYPE_CHECKING
from typing import Any
from typing import TextIO

import pytest

from poetry.core.factory import Factory
from poetry.core.masonry.builders.wheel import WheelBuilder


if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock import MockerFixture

    from tests.types import FixtureFactory


WHEEL_TAG_REGEX = "[cp]p[23]_?\\d+-(?:cp[23]_?\\d+m?u?|pypy[23]_?\\d+_pp\\d+)-.+"

shared_lib_extensions = importlib.machinery.EXTENSION_SUFFIXES


def test_wheel_module(fixture_factory: FixtureFactory) -> None:
    fixture = fixture_factory("module1")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = fixture / "dist" / "module1-0.1-py2.py3-none-any.whl"
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "module1.py" in zipf.namelist()


@pytest.mark.filterwarnings("ignore:.* script .* extra:DeprecationWarning")
def test_wheel_package(fixture_factory: FixtureFactory) -> None:
    fixture = fixture_factory("complete")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    fixture = fixture / "dist" / "my_package-1.2.3-py3-none-any.whl"
    assert fixture.exists()

    with zipfile.ZipFile(fixture) as zipf:
        assert "my_package/sub_pkg1/__init__.py" in zipf.namelist()


def test_wheel_prerelease(fixture_factory: FixtureFactory) -> None:
    fixture = fixture_factory("prerelease")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = fixture / "dist" / "prerelease-0.1b1-py2.py3-none-any.whl"
    assert bdist.exists()


def test_wheel_epoch(fixture_factory: FixtureFactory) -> None:
    fixture = fixture_factory("epoch")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = fixture / "dist" / "epoch-1!2.0-py2.py3-none-any.whl"
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "epoch-1!2.0.dist-info/METADATA" in zipf.namelist()


def test_wheel_excluded_data(fixture_factory: FixtureFactory) -> None:
    fixture = fixture_factory("default_with_excluded_data_toml")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = fixture / "dist" / "my_package-1.2.3-py3-none-any.whl"
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "my_package/__init__.py" in zipf.namelist()
        assert "my_package/data/sub_data/data2.txt" in zipf.namelist()
        assert "my_package/data/sub_data/data3.txt" in zipf.namelist()
        assert "my_package/data/data1.txt" not in zipf.namelist()


def test_wheel_excluded_nested_data(fixture_factory: FixtureFactory) -> None:
    fixture = fixture_factory("exclude_nested_data_toml")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = fixture / "dist" / "my_package-1.2.3-py3-none-any.whl"
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "my_package/__init__.py" in zipf.namelist()
        assert "my_package/data/sub_data/data2.txt" not in zipf.namelist()
        assert "my_package/data/sub_data/data3.txt" not in zipf.namelist()
        assert "my_package/data/data1.txt" not in zipf.namelist()
        assert "my_package/data/data2.txt" in zipf.namelist()
        assert "my_package/public/publicdata.txt" in zipf.namelist()
        assert "my_package/public/item1/itemdata1.txt" not in zipf.namelist()
        assert "my_package/public/item1/subitem/subitemdata.txt" not in zipf.namelist()
        assert "my_package/public/item2/itemdata2.txt" not in zipf.namelist()


def test_include_excluded_code(fixture_factory: FixtureFactory) -> None:
    fixture = fixture_factory("include_excluded_code")
    poetry = Factory().create_poetry(fixture)

    wb = WheelBuilder(poetry)
    wb.build()

    bdist = fixture / "dist" / wb.wheel_filename
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "my_package/__init__.py" in zipf.namelist()
        assert "my_package/generated.py" in zipf.namelist()
        assert "lib/my_package/generated.py" not in zipf.namelist()


def test_wheel_localversionlabel(fixture_factory: FixtureFactory) -> None:
    fixture = fixture_factory("localversionlabel")
    project = Factory().create_poetry(fixture)

    WheelBuilder.make(project)

    local_version_string = "localversionlabel-0.1b1+gitbranch.buildno.1"

    bdist = fixture / "dist" / (local_version_string + "-py2.py3-none-any.whl")
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert local_version_string + ".dist-info/METADATA" in zipf.namelist()


def test_wheel_package_src(fixture_factory: FixtureFactory) -> None:
    fixture = fixture_factory("source_package")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = fixture / "dist" / "package_src-0.1-py2.py3-none-any.whl"
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "package_src/__init__.py" in zipf.namelist()
        assert "package_src/module.py" in zipf.namelist()


def test_wheel_module_src(fixture_factory: FixtureFactory) -> None:
    fixture = fixture_factory("source_file")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = fixture / "dist" / "module_src-0.1-py2.py3-none-any.whl"
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "module_src.py" in zipf.namelist()


def test_wheel_build_script_creates_package(fixture_factory: FixtureFactory) -> None:
    fixture = fixture_factory("build_script_creates_package")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    # Currently, if a build.py script is used,
    # poetry just assumes the most specific tags
    bdist = next((fixture / "dist").glob("my_package-0.1-*.whl"))
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "my_package/__init__.py" in zipf.namelist()
        assert "my_package/foo.py" in zipf.namelist()


@pytest.mark.filterwarnings("ignore:.* script .* extra:DeprecationWarning")
def test_dist_info_file_permissions(fixture_factory: FixtureFactory) -> None:
    fixture = fixture_factory("complete")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = fixture / "dist" / "my_package-1.2.3-py3-none-any.whl"
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert (
            zipf.getinfo("my_package-1.2.3.dist-info/WHEEL").external_attr & 0x1FF0000
            == 0o644 << 16
        )
        assert (
            zipf.getinfo("my_package-1.2.3.dist-info/METADATA").external_attr
            & 0x1FF0000
            == 0o644 << 16
        )
        assert (
            zipf.getinfo("my_package-1.2.3.dist-info/RECORD").external_attr & 0x1FF0000
            == 0o644 << 16
        )
        assert (
            zipf.getinfo("my_package-1.2.3.dist-info/entry_points.txt").external_attr
            & 0x1FF0000
            == 0o644 << 16
        )


def test_wheel_includes_inline_table(fixture_factory: FixtureFactory) -> None:
    fixture = fixture_factory("with_include_inline_table")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = fixture / "dist" / "with_include-1.2.3-py3-none-any.whl"
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "both.txt" in zipf.namelist()
        assert "wheel_only.txt" in zipf.namelist()
        assert "notes.txt" not in zipf.namelist()


@pytest.mark.parametrize(
    "fixture_name",
    ["pep_561_stub_only", "pep_561_stub_only_partial", "pep_561_stub_only_src"],
)
def test_wheel_package_pep_561_stub_only(
    fixture_name: str, fixture_factory: FixtureFactory
) -> None:
    fixture = fixture_factory(fixture_name)
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = fixture / "dist" / "pep_561_stubs-0.1-py3-none-any.whl"
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "pkg-stubs/__init__.pyi" in zipf.namelist()
        assert "pkg-stubs/module.pyi" in zipf.namelist()
        assert "pkg-stubs/subpkg/__init__.pyi" in zipf.namelist()


def test_wheel_package_pep_561_stub_only_partial_namespace(
    fixture_factory: FixtureFactory,
) -> None:
    fixture = fixture_factory("pep_561_stub_only_partial_namespace")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = fixture / "dist" / "pep_561_stubs-0.1-py3-none-any.whl"
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "pkg-stubs/module.pyi" in zipf.namelist()
        assert "pkg-stubs/subpkg/__init__.pyi" in zipf.namelist()
        assert "pkg-stubs/subpkg/py.typed" in zipf.namelist()


def test_wheel_package_pep_561_stub_only_includes_typed_marker(
    fixture_factory: FixtureFactory,
) -> None:
    fixture = fixture_factory("pep_561_stub_only_partial")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = fixture / "dist" / "pep_561_stubs-0.1-py3-none-any.whl"
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "pkg-stubs/py.typed" in zipf.namelist()


def test_wheel_includes_licenses_in_correct_paths(
    fixture_factory: FixtureFactory,
) -> None:
    fixture = fixture_factory("licenses_and_copying")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = fixture / "dist" / "my_package-1.2.3-py3-none-any.whl"
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "my_package-1.2.3.dist-info/COPYING" in zipf.namelist()
        assert "my_package-1.2.3.dist-info/COPYING.txt" in zipf.namelist()
        assert "my_package-1.2.3.dist-info/LICENSE" in zipf.namelist()
        assert "my_package-1.2.3.dist-info/LICENSE.md" in zipf.namelist()
        assert "my_package-1.2.3.dist-info/LICENSES/CUSTOM-LICENSE" in zipf.namelist()
        assert "my_package-1.2.3.dist-info/LICENSES/BSD-3.md" in zipf.namelist()
        assert "my_package-1.2.3.dist-info/LICENSES/MIT.txt" in zipf.namelist()


def test_wheel_with_file_with_comma(fixture_factory: FixtureFactory) -> None:
    fixture = fixture_factory("comma_file")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = fixture / "dist" / "comma_file-1.2.3-py3-none-any.whl"
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        records = zipf.read("comma_file-1.2.3.dist-info/RECORD")
        assert '\n"comma_file/a,b.py"' in records.decode()


def test_default_src_with_excluded_data(
    fixture_factory: FixtureFactory, mocker: MockerFixture
) -> None:
    class MockGit:
        def get_ignored_files(self, folder: Path | None = None) -> list[str]:
            # Patch git module to return specific excluded files
            return [
                "src/my_package/data/sub_data/data2.txt",
            ]

    p = mocker.patch("poetry.core.vcs.get_vcs")
    p.return_value = MockGit()

    fixture = fixture_factory("default_src_with_excluded_data")
    poetry = Factory().create_poetry(fixture)

    builder = WheelBuilder(poetry)
    builder.build()

    bdist = fixture / "dist" / "my_package-1.2.3-py3-none-any.whl"
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "my_package/__init__.py" in zipf.namelist()
        assert "my_package/data/data1.txt" in zipf.namelist()
        assert "my_package/data/sub_data/data2.txt" not in zipf.namelist()
        assert "my_package/data/sub_data/data3.txt" in zipf.namelist()


def test_wheel_file_is_closed(
    fixture_factory: FixtureFactory, monkeypatch: MonkeyPatch
) -> None:
    """Confirm that wheel zip files are explicitly closed."""
    fd_file: TextIO | None = None
    real_fdopen = os.fdopen

    def capturing_fdopen(*args: Any, **kwargs: Any) -> TextIO | None:
        nonlocal fd_file
        fd_file = real_fdopen(*args, **kwargs)
        return fd_file

    monkeypatch.setattr("os.fdopen", capturing_fdopen)

    fixture = fixture_factory("module1")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    assert fd_file is not None
    assert fd_file.closed


@pytest.mark.parametrize("in_venv_build", [True, False])
def test_tag(
    in_venv_build: bool, fixture_factory: FixtureFactory, mocker: MockerFixture
) -> None:
    """
    Tests that tag returns a valid tag if a build script is used,
    no matter if poetry-core lives inside the build environment or not.
    """
    fixture = fixture_factory("extended")
    poetry = Factory().create_poetry(fixture)
    builder = WheelBuilder(poetry)

    get_sys_tags_spy = mocker.spy(builder, "_get_sys_tags")
    if not in_venv_build:
        mocker.patch("sys.executable", "other/python")

    assert re.match(f"^{WHEEL_TAG_REGEX}$", builder.tag)
    if in_venv_build:
        get_sys_tags_spy.assert_not_called()
    else:
        get_sys_tags_spy.assert_called()


def test_extended_editable_wheel_build(fixture_factory: FixtureFactory) -> None:
    """
    Tests that an editable wheel made from a project with extensions includes
    the .pth, but does not include the built package itself.
    """
    fixture = fixture_factory("extended")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make_in(poetry, editable=True)

    bdist = next((fixture / "dist").glob("extended-0.1-*.whl"))

    assert bdist.exists()
    with zipfile.ZipFile(bdist) as zipf:
        assert "extended.pth" in zipf.namelist()
        # Ensure the directory "extended/" does not exist in the whl
        assert all(not n.startswith("extended/") for n in zipf.namelist())


def test_extended_editable_build_inplace(fixture_factory: FixtureFactory) -> None:
    """
    Tests that a project with extensions builds the extension modules in-place
    when ran for an editable install.
    """
    fixture = fixture_factory("extended")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make_in(poetry, editable=True)

    # Check that an extension with any of the allowed extensions was built in-place
    assert any(
        (fixture / "extended" / f"extended{ext}").exists()
        for ext in shared_lib_extensions
    )


def test_build_py_only_included(fixture_factory: FixtureFactory) -> None:
    """
    Tests that a build.py that only defined the command build_py (which generates a
    lib folder) will have its artifacts included.
    """
    fixture = fixture_factory("build_with_build_py_only")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = next((fixture / "dist").glob("build_with_build_py_only-0.1-*.whl"))
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "build_with_build_py_only/generated/file.py" in zipf.namelist()


def test_generated_script_file(fixture_factory: FixtureFactory) -> None:
    """Tests that a file that is generated by build.py can be used as script."""
    fixture = fixture_factory("generated_script_file")
    poetry = Factory().create_poetry(fixture)

    WheelBuilder.make(poetry)

    bdist = next((fixture / "dist").glob("generated_script_file-0.1-*.whl"))
    assert bdist.exists()

    with zipfile.ZipFile(bdist) as zipf:
        assert "generated_script_file-0.1.data/scripts/script.sh" in zipf.namelist()
