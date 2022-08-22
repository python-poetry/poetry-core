from __future__ import annotations

from pathlib import Path

import pytest

from poetry.core.masonry.utils.package_include import PackageInclude


fixtures_dir = Path(__file__).parent / "fixtures"
with_includes = fixtures_dir / "with_includes"


def test_package_include_with_multiple_dirs() -> None:
    pkg_include = PackageInclude(base=fixtures_dir, include="with_includes")
    assert pkg_include.elements == [
        with_includes / "__init__.py",
        with_includes / "bar",
        with_includes / "bar/baz.py",
        with_includes / "extra_package",
        with_includes / "extra_package/some_dir",
        with_includes / "extra_package/some_dir/foo.py",
        with_includes / "extra_package/some_dir/quux.py",
        with_includes / "not_a_python_pkg",
        with_includes / "not_a_python_pkg/baz.txt",
    ]


def test_package_include_with_simple_dir() -> None:
    pkg_include = PackageInclude(base=with_includes, include="bar")
    assert pkg_include.elements == [with_includes / "bar/baz.py"]


def test_package_include_with_nested_dir() -> None:
    pkg_include = PackageInclude(base=with_includes, include="extra_package/**/*.py")
    assert pkg_include.elements == [
        with_includes / "extra_package/some_dir/foo.py",
        with_includes / "extra_package/some_dir/quux.py",
    ]


def test_package_include_with_no_python_files_in_dir() -> None:
    with pytest.raises(ValueError) as e:
        PackageInclude(base=with_includes, include="not_a_python_pkg")

    assert str(e.value) == "not_a_python_pkg is not a package."


def test_package_include_with_non_existent_directory() -> None:
    with pytest.raises(ValueError) as e:
        PackageInclude(base=with_includes, include="not_a_dir")

    err_str = str(with_includes / "not_a_dir") + " does not contain any element"

    assert str(e.value) == err_str


def test_pep_561_stub_only_package_good_name_suffix() -> None:
    pkg_include = PackageInclude(
        base=fixtures_dir / "pep_561_stub_only", include="good-stubs"
    )
    assert pkg_include.elements == [
        fixtures_dir / "pep_561_stub_only/good-stubs/__init__.pyi",
        fixtures_dir / "pep_561_stub_only/good-stubs/module.pyi",
    ]


def test_pep_561_stub_only_partial_namespace_package_good_name_suffix() -> None:
    pkg_include = PackageInclude(
        base=fixtures_dir / "pep_561_stub_only_partial_namespace", include="good-stubs"
    )
    assert pkg_include.elements == [
        fixtures_dir / "pep_561_stub_only_partial_namespace/good-stubs/module.pyi",
        fixtures_dir / "pep_561_stub_only_partial_namespace/good-stubs/subpkg/",
        fixtures_dir
        / "pep_561_stub_only_partial_namespace/good-stubs/subpkg/__init__.pyi",
        fixtures_dir / "pep_561_stub_only_partial_namespace/good-stubs/subpkg/py.typed",
    ]


def test_pep_561_stub_only_package_bad_name_suffix() -> None:
    with pytest.raises(ValueError) as e:
        PackageInclude(base=fixtures_dir / "pep_561_stub_only", include="bad")

    assert str(e.value) == "bad is not a package."
