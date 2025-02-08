from __future__ import annotations

import ast
import gzip
import hashlib
import logging
import shutil
import tarfile

from email.parser import Parser
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

import pytest

from packaging.utils import canonicalize_name

from poetry.core.factory import Factory
from poetry.core.masonry.builders.sdist import SdistBuilder
from poetry.core.masonry.utils.package_include import PackageInclude
from poetry.core.packages.dependency import Dependency
from poetry.core.packages.project_package import ProjectPackage
from poetry.core.packages.vcs_dependency import VCSDependency


if TYPE_CHECKING:
    from collections.abc import Iterator

    from pytest import LogCaptureFixture
    from pytest import MonkeyPatch
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


def project(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / name


def test_convert_dependencies() -> None:
    package = ProjectPackage("foo", "1.2.3")
    result = SdistBuilder.convert_dependencies(
        package,
        [
            Dependency("A", "^1.0"),
            Dependency("B", "~1.0"),
            Dependency("C", "1.2.3"),
            VCSDependency("D", "git", "https://github.com/sdispater/d.git"),
            Dependency("E", "^1.0"),
            Dependency("F", "^1.0,!=1.3"),
        ],
    )
    main = [
        "A>=1.0,<2.0",
        "B>=1.0,<1.1",
        "C==1.2.3",
        "D @ git+https://github.com/sdispater/d.git",
        "E>=1.0,<2.0",
        "F>=1.0,<2.0,!=1.3",
    ]
    extras: dict[str, Any] = {}

    assert result == (main, extras)

    package = ProjectPackage("foo", "1.2.3")
    package.extras = {canonicalize_name("bar"): [Dependency("A", "*")]}

    result = SdistBuilder.convert_dependencies(
        package,
        [
            Dependency("A", ">=1.2", optional=True),
            Dependency("B", "~1.0"),
            Dependency("C", "1.2.3"),
        ],
    )
    main = ["B>=1.0,<1.1", "C==1.2.3"]
    extras = {"bar": ["A>=1.2"]}

    assert result == (main, extras)

    c = Dependency("C", "1.2.3")
    c.python_versions = "~2.7 || ^3.6"
    d = Dependency("D", "3.4.5", optional=True)
    d.python_versions = "~2.7 || ^3.4"

    package.extras = {canonicalize_name("baz"): [Dependency("D", "*")]}

    result = SdistBuilder.convert_dependencies(
        package,
        [Dependency("A", ">=1.2", optional=True), Dependency("B", "~1.0"), c, d],
    )
    main = ["B>=1.0,<1.1"]

    extra_python = (
        ':python_version == "2.7" or python_version >= "3.6" and python_version < "4.0"'
    )
    extra_d_dependency = (
        'baz:python_version == "2.7" '
        'or python_version >= "3.4" and python_version < "4.0"'
    )
    extras = {extra_python: ["C==1.2.3"], extra_d_dependency: ["D==3.4.5"]}

    assert result == (main, extras)


@pytest.mark.parametrize(
    "project_name", ["complete", "complete_new", "complete_dynamic"]
)
def test_make_setup(project_name: str) -> None:
    poetry = Factory().create_poetry(project(project_name))

    builder = SdistBuilder(poetry)
    setup = builder.build_setup()
    setup_ast = ast.parse(setup)

    setup_ast.body = [n for n in setup_ast.body if isinstance(n, ast.Assign)]
    ns: dict[str, Any] = {}
    exec(compile(setup_ast, filename="setup.py", mode="exec"), ns)
    assert ns["packages"] == [
        "my_package",
        "my_package.sub_pkg1",
        "my_package.sub_pkg2",
        "my_package.sub_pkg3",
    ]
    assert ns["install_requires"] == ["cachy[msgpack]>=0.2.0,<0.3.0", "cleo>=0.6,<0.7"]
    assert ns["entry_points"] == {
        "console_scripts": [
            "extra-script = my_package.extra:main",
            "my-2nd-script = my_package:main2",
            "my-script = my_package:main",
        ],
        "poetry.application.plugin": [
            "my-command = my_package.plugins:MyApplicationPlugin"
        ],
    }
    assert ns["scripts"] == [str(Path("bin") / "script.sh")]
    assert ns["extras_require"] == {
        'time:python_version ~= "2.7" and sys_platform == "win32" or python_version in "3.4 3.5"': [
            "pendulum>=1.4,<2.0"
        ]
    }


@pytest.mark.parametrize(
    "project_name", ["complete", "complete_new", "complete_dynamic"]
)
def test_make_pkg_info(project_name: str, mocker: MockerFixture) -> None:
    get_metadata_content = mocker.patch(
        "poetry.core.masonry.builders.builder.Builder.get_metadata_content"
    )
    poetry = Factory().create_poetry(project(project_name))

    builder = SdistBuilder(poetry)
    builder.build_pkg_info()

    assert get_metadata_content.called


def test_make_pkg_info_any_python() -> None:
    poetry = Factory().create_poetry(project("module1"))

    builder = SdistBuilder(poetry)
    pkg_info = builder.build_pkg_info()
    p = Parser()
    parsed = p.parsestr(pkg_info.decode())

    assert "Requires-Python" not in parsed


@pytest.mark.parametrize(
    "project_name", ["complete", "complete_new", "complete_dynamic"]
)
def test_find_files_to_add(project_name: str) -> None:
    poetry = Factory().create_poetry(project(project_name))

    builder = SdistBuilder(poetry)
    result = {f.relative_to_source_root() for f in builder.find_files_to_add()}

    assert result == {
        Path("AUTHORS"),
        Path("COPYING"),
        Path("LICENCE"),
        Path("LICENSE"),
        Path("README.rst"),
        Path("bin/script.sh"),
        Path("my_package/__init__.py"),
        Path("my_package/data1/test.json"),
        Path("my_package/sub_pkg1/__init__.py"),
        Path("my_package/sub_pkg2/__init__.py"),
        Path("my_package/sub_pkg2/data2/data.json"),
        Path("my_package/sub_pkg3/foo.py"),
        Path("pyproject.toml"),
    }


def test_find_files_to_add_with_multiple_readme_files() -> None:
    poetry = Factory().create_poetry(
        Path(__file__).parent.parent.parent / "fixtures" / "with_readme_files"
    )

    builder = SdistBuilder(poetry)
    result = {f.relative_to_source_root() for f in builder.find_files_to_add()}

    assert result == {
        Path("README-1.rst"),
        Path("README-2.rst"),
        Path("my_package/__init__.py"),
        Path("pyproject.toml"),
    }


def test_make_pkg_info_multi_constraints_dependency() -> None:
    poetry = Factory().create_poetry(
        Path(__file__).parent.parent.parent
        / "fixtures"
        / "project_with_multi_constraints_dependency"
    )

    builder = SdistBuilder(poetry)
    pkg_info = builder.build_pkg_info()
    p = Parser()
    parsed = p.parsestr(pkg_info.decode())

    requires = parsed.get_all("Requires-Dist")
    assert requires == [
        'pendulum (>=1.5,<2.0) ; python_version < "3.4"',
        'pendulum (>=2.0,<3.0) ; python_version >= "3.4" and python_version < "4.0"',
    ]


@pytest.mark.parametrize(
    "project_name", ["complete", "complete_new", "complete_dynamic"]
)
def test_find_packages(project_name: str) -> None:
    poetry = Factory().create_poetry(project(project_name))

    builder = SdistBuilder(poetry)

    base = project(project_name)
    include = PackageInclude(base, "my_package", formats=["sdist"])

    pkg_dir, packages, pkg_data = builder.find_packages(include)

    assert pkg_dir is None
    assert packages == [
        "my_package",
        "my_package.sub_pkg1",
        "my_package.sub_pkg2",
        "my_package.sub_pkg3",
    ]
    assert pkg_data == {
        "": ["*"],
        "my_package": ["data1/*"],
        "my_package.sub_pkg2": ["data2/*"],
    }

    poetry = Factory().create_poetry(project("source_package"))

    builder = SdistBuilder(poetry)

    base = project("source_package")
    include = PackageInclude(base, "package_src", source="src", formats=["sdist"])

    pkg_dir, packages, pkg_data = builder.find_packages(include)

    assert pkg_dir == str(base / "src")
    assert packages == ["package_src"]
    assert pkg_data == {"": ["*"]}


@pytest.mark.parametrize(
    "project_name", ["complete", "complete_new", "complete_dynamic"]
)
def test_package(project_name: str) -> None:
    poetry = Factory().create_poetry(project(project_name))

    builder = SdistBuilder(poetry)
    builder.build()

    sdist = fixtures_dir / project_name / "dist" / "my_package-1.2.3.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "my_package-1.2.3/LICENSE" in tar.getnames()


@pytest.mark.parametrize("target_dir", [None, "dist", "dist/build"])
def test_package_target_dir(tmp_path: Path, target_dir: str | None) -> None:
    poetry = Factory().create_poetry(project("complete"))

    builder = SdistBuilder(poetry)
    builder.build(target_dir=tmp_path / target_dir if target_dir else None)

    sdist = (
        tmp_path / target_dir if target_dir else fixtures_dir / "complete" / "dist"
    ) / "my_package-1.2.3.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "my_package-1.2.3/LICENSE" in tar.getnames()


@pytest.mark.parametrize(
    "project_name", ["complete", "complete_new", "complete_dynamic"]
)
def test_sdist_reproducibility(project_name: str) -> None:
    poetry = Factory().create_poetry(project(project_name))

    hashes = set()

    for _ in range(2):
        builder = SdistBuilder(poetry)
        builder.build()

        sdist = fixtures_dir / project_name / "dist" / "my_package-1.2.3.tar.gz"

        assert sdist.exists()

        hashes.add(hashlib.sha256(sdist.read_bytes()).hexdigest())

    assert len(hashes) == 1


@pytest.mark.parametrize(
    "project_name", ["complete", "complete_new", "complete_dynamic"]
)
def test_setup_py_context(project_name: str) -> None:
    poetry = Factory().create_poetry(project(project_name))

    builder = SdistBuilder(poetry)

    project_setup_py = poetry.pyproject_path.parent / "setup.py"

    assert not project_setup_py.exists()

    try:
        with builder.setup_py() as setup:
            assert setup.exists()
            assert project_setup_py == setup

            with setup.open(mode="rb") as f:
                # we convert to string  and replace line endings here for compatibility
                data = f.read().decode().replace("\r\n", "\n")
                assert data == builder.build_setup().decode()

        assert not project_setup_py.exists()
    finally:
        if project_setup_py.exists():
            project_setup_py.unlink()


def test_module() -> None:
    poetry = Factory().create_poetry(project("module1"))

    builder = SdistBuilder(poetry)
    builder.build()

    sdist = fixtures_dir / "module1" / "dist" / "module1-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "module1-0.1/module1.py" in tar.getnames()


def test_prelease() -> None:
    poetry = Factory().create_poetry(project("prerelease"))

    builder = SdistBuilder(poetry)
    builder.build()

    sdist = fixtures_dir / "prerelease" / "dist" / "prerelease-0.1b1.tar.gz"

    assert sdist.exists()


@pytest.mark.parametrize("directory", ["extended", "extended_legacy_config"])
def test_with_c_extensions(directory: str) -> None:
    poetry = Factory().create_poetry(project("extended"))

    builder = SdistBuilder(poetry)
    builder.build()

    sdist = fixtures_dir / "extended" / "dist" / "extended-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "extended-0.1/build.py" in tar.getnames()
        assert "extended-0.1/extended/extended.c" in tar.getnames()


def test_with_c_extensions_src_layout() -> None:
    poetry = Factory().create_poetry(project("src_extended"))

    builder = SdistBuilder(poetry)
    builder.build()

    sdist = fixtures_dir / "src_extended" / "dist" / "extended-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "extended-0.1/build.py" in tar.getnames()
        assert "extended-0.1/src/extended/extended.c" in tar.getnames()


def test_with_build_script_in_subdir() -> None:
    poetry = Factory().create_poetry(project("build_script_in_subdir"))

    builder = SdistBuilder(poetry)
    setup = builder.build_setup()
    # should not error
    ast.parse(setup)


def test_with_src_module_file() -> None:
    poetry = Factory().create_poetry(project("source_file"))

    builder = SdistBuilder(poetry)

    # Check setup.py
    setup = builder.build_setup()
    setup_ast = ast.parse(setup)

    setup_ast.body = [n for n in setup_ast.body if isinstance(n, ast.Assign)]
    ns: dict[str, Any] = {}
    exec(compile(setup_ast, filename="setup.py", mode="exec"), ns)
    assert ns["package_dir"] == {"": "src"}
    assert ns["modules"] == ["module_src"]

    builder.build()

    sdist = fixtures_dir / "source_file" / "dist" / "module_src-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "module_src-0.1/src/module_src.py" in tar.getnames()


def test_with_src_module_dir() -> None:
    poetry = Factory().create_poetry(project("source_package"))

    builder = SdistBuilder(poetry)

    # Check setup.py
    setup = builder.build_setup()
    setup_ast = ast.parse(setup)

    setup_ast.body = [n for n in setup_ast.body if isinstance(n, ast.Assign)]
    ns: dict[str, Any] = {}
    exec(compile(setup_ast, filename="setup.py", mode="exec"), ns)
    assert ns["package_dir"] == {"": "src"}
    assert ns["packages"] == ["package_src"]

    builder.build()

    sdist = fixtures_dir / "source_package" / "dist" / "package_src-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "package_src-0.1/src/package_src/__init__.py" in tar.getnames()
        assert "package_src-0.1/src/package_src/module.py" in tar.getnames()


def test_default_with_excluded_data(mocker: MockerFixture) -> None:
    mocker.patch(
        "poetry.core.vcs.git.Git.get_ignored_files",
        return_value=["my_package/data/sub_data/data2.txt"],
    )
    poetry = Factory().create_poetry(project("default_with_excluded_data"))

    builder = SdistBuilder(poetry)

    # Check setup.py
    setup = builder.build_setup()
    setup_ast = ast.parse(setup)

    setup_ast.body = [n for n in setup_ast.body if isinstance(n, ast.Assign)]
    ns: dict[str, Any] = {}
    exec(compile(setup_ast, filename="setup.py", mode="exec"), ns)
    assert "package_dir" not in ns
    assert ns["packages"] == ["my_package"]
    assert ns["package_data"] == {
        "": ["*"],
        "my_package": ["data/*", "data/sub_data/data3.txt"],
    }

    builder.build()

    sdist = (
        fixtures_dir / "default_with_excluded_data" / "dist" / "my_package-1.2.3.tar.gz"
    )

    assert sdist.exists()
    with tarfile.open(str(sdist), "r") as tar:
        names = tar.getnames()
        assert len(names) == len(set(names))
        assert "my_package-1.2.3/LICENSE" in names
        assert "my_package-1.2.3/README.rst" in names
        assert "my_package-1.2.3/my_package/__init__.py" in names
        assert "my_package-1.2.3/my_package/data/data1.txt" in names
        assert "my_package-1.2.3/pyproject.toml" in names
        assert "my_package-1.2.3/PKG-INFO" in names


def test_src_excluded_nested_data() -> None:
    module_path = fixtures_dir / "exclude_nested_data_toml"
    poetry = Factory().create_poetry(module_path)

    builder = SdistBuilder(poetry)
    builder.build()

    sdist = module_path / "dist" / "my_package-1.2.3.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        names = tar.getnames()
        assert len(names) == len(set(names))
        assert "my_package-1.2.3/LICENSE" in names
        assert "my_package-1.2.3/README.rst" in names
        assert "my_package-1.2.3/pyproject.toml" in names
        assert "my_package-1.2.3/PKG-INFO" in names
        assert "my_package-1.2.3/my_package/__init__.py" in names
        assert "my_package-1.2.3/my_package/data/sub_data/data2.txt" not in names
        assert "my_package-1.2.3/my_package/data/sub_data/data3.txt" not in names
        assert "my_package-1.2.3/my_package/data/data1.txt" not in names
        assert "my_package-1.2.3/my_package/data/data2.txt" in names
        assert "my_package-1.2.3/my_package/puplic/publicdata.txt" in names
        assert "my_package-1.2.3/my_package/public/item1/itemdata1.txt" not in names
        assert (
            "my_package-1.2.3/my_package/public/item1/subitem/subitemdata.txt"
            not in names
        )
        assert "my_package-1.2.3/my_package/public/item2/itemdata2.txt" not in names


def test_proper_python_requires_if_two_digits_precision_version_specified() -> None:
    poetry = Factory().create_poetry(project("simple_version"))

    builder = SdistBuilder(poetry)
    pkg_info = builder.build_pkg_info()
    p = Parser()
    parsed = p.parsestr(pkg_info.decode())

    assert parsed["Requires-Python"] == ">=3.6,<3.7"


def test_proper_python_requires_if_three_digits_precision_version_specified() -> None:
    poetry = Factory().create_poetry(project("single_python"))

    builder = SdistBuilder(poetry)
    pkg_info = builder.build_pkg_info()
    p = Parser()
    parsed = p.parsestr(pkg_info.decode())

    assert parsed["Requires-Python"] == "==2.7.15"


def test_sdist_does_not_include_pycache_and_pyc_files(
    complete_with_pycache_and_pyc_files: Path,
) -> None:
    poetry = Factory().create_poetry(complete_with_pycache_and_pyc_files)

    builder = SdistBuilder(poetry)

    builder.build()

    sdist = complete_with_pycache_and_pyc_files / "dist" / "my_package-1.2.3.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        for name in tar.getnames():
            assert "__pycache__" not in name
            assert not name.endswith(".pyc")


def test_includes() -> None:
    poetry = Factory().create_poetry(project("with-include"))

    builder = SdistBuilder(poetry)

    builder.build()

    sdist = fixtures_dir / "with-include" / "dist" / "with_include-1.2.3.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "with_include-1.2.3/extra_dir/vcs_excluded.py" in tar.getnames()
        assert "with_include-1.2.3/notes.txt" in tar.getnames()


def test_include_formats() -> None:
    poetry = Factory().create_poetry(project("with-include-formats"))

    builder = SdistBuilder(poetry)

    builder.build()

    sdist = fixtures_dir / "with-include-formats" / "dist" / "with_include-1.2.3.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        # packages
        assert "with_include-1.2.3/src/mod_default.py" in tar.getnames()
        assert "with_include-1.2.3/src/mod_sdist_only.py" in tar.getnames()
        assert "with_include-1.2.3/src/mod_wheel_only.py" not in tar.getnames()
        assert "with_include-1.2.3/src/mod_both.py" in tar.getnames()
        assert "with_include-1.2.3/src/pkg_default/__init__.py" in tar.getnames()
        assert "with_include-1.2.3/src/pkg_default/sub/__init__.py" in tar.getnames()
        assert "with_include-1.2.3/src/pkg_sdist_only/__init__.py" in tar.getnames()
        assert "with_include-1.2.3/src/pkg_sdist_only/sub/__init__.py" in tar.getnames()
        assert "with_include-1.2.3/src/pkg_wheel_only/__init__.py" not in tar.getnames()
        assert (
            "with_include-1.2.3/src/pkg_wheel_only/sub/__init__.py"
            not in tar.getnames()
        )
        assert "with_include-1.2.3/src/pkg_both/__init__.py" in tar.getnames()
        assert "with_include-1.2.3/src/pkg_both/sub/__init__.py" in tar.getnames()
        # other includes
        assert "with_include-1.2.3/default.txt" in tar.getnames()
        assert "with_include-1.2.3/sdist_only.txt" in tar.getnames()
        assert "with_include-1.2.3/wheel_only.txt" not in tar.getnames()
        assert "with_include-1.2.3/both.txt" in tar.getnames()
        assert "with_include-1.2.3/default/file.txt" in tar.getnames()
        assert "with_include-1.2.3/default/sub/file.txt" in tar.getnames()
        assert "with_include-1.2.3/sdist_only/file.txt" in tar.getnames()
        assert "with_include-1.2.3/sdist_only/sub/file.txt" in tar.getnames()
        assert "with_include-1.2.3/wheel_only/file.txt" not in tar.getnames()
        assert "with_include-1.2.3/wheel_only/sub/file.txt" not in tar.getnames()
        assert "with_include-1.2.3/both/file.txt" in tar.getnames()
        assert "with_include-1.2.3/both/sub/file.txt" in tar.getnames()


def test_excluded_subpackage() -> None:
    poetry = Factory().create_poetry(project("excluded_subpackage"))

    builder = SdistBuilder(poetry)
    setup = builder.build_setup()

    setup_ast = ast.parse(setup)

    setup_ast.body = [n for n in setup_ast.body if isinstance(n, ast.Assign)]
    ns: dict[str, Any] = {}
    exec(compile(setup_ast, filename="setup.py", mode="exec"), ns)

    assert ns["packages"] == ["example"]


def test_sdist_package_pep_561_stub_only() -> None:
    root = fixtures_dir / "pep_561_stub_only"
    poetry = Factory().create_poetry(root)

    builder = SdistBuilder(poetry)
    builder.build()

    sdist = root / "dist" / "pep_561_stubs-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        names = tar.getnames()
        assert "pep_561_stubs-0.1/pkg-stubs/__init__.pyi" in names
        assert "pep_561_stubs-0.1/pkg-stubs/module.pyi" in names
        assert "pep_561_stubs-0.1/pkg-stubs/subpkg/__init__.pyi" in names


def test_sdist_disable_setup_py() -> None:
    module_path = fixtures_dir / "disable_setup_py"
    poetry = Factory().create_poetry(module_path)

    builder = SdistBuilder(poetry)
    builder.build()

    sdist = module_path / "dist" / "my_package-1.2.3.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert set(tar.getnames()) == {
            "my_package-1.2.3/README.rst",
            "my_package-1.2.3/pyproject.toml",
            "my_package-1.2.3/PKG-INFO",
            "my_package-1.2.3/my_package/__init__.py",
        }


def test_sdist_mtime_zero() -> None:
    poetry = Factory().create_poetry(project("module1"))

    builder = SdistBuilder(poetry)
    builder.build()

    sdist = fixtures_dir / "module1" / "dist" / "module1-0.1.tar.gz"

    assert sdist.exists()

    with gzip.open(str(sdist), "rb") as gz:
        gz.read(100)
        assert gz.mtime == 0


def test_split_source() -> None:
    root = fixtures_dir / "split_source"
    poetry = Factory().create_poetry(root)

    builder = SdistBuilder(poetry)

    # Check setup.py
    setup = builder.build_setup()
    setup_ast = ast.parse(setup)

    setup_ast.body = [n for n in setup_ast.body if isinstance(n, ast.Assign)]
    ns: dict[str, Any] = {}
    exec(compile(setup_ast, filename="setup.py", mode="exec"), ns)
    assert "" in ns["package_dir"] and "module_b" in ns["package_dir"]


@pytest.mark.parametrize("log_level", [logging.INFO, logging.DEBUG])
def test_sdist_members_mtime_default(caplog: LogCaptureFixture, log_level: int) -> None:
    caplog.set_level(log_level)
    poetry = Factory().create_poetry(project("module1"))

    builder = SdistBuilder(poetry)
    builder.build()

    sdist = fixtures_dir / "module1" / "dist" / "module1-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        for tarinfo in tar.getmembers():
            assert tarinfo.mtime == 0

    source_data_epoch_message = (
        "SOURCE_DATE_EPOCH environment variable is not set, using mtime=0"
    )
    if log_level == logging.DEBUG:
        assert source_data_epoch_message in caplog.messages
    else:
        assert source_data_epoch_message not in caplog.messages


def test_sdist_mtime_set_from_envvar(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1727883000")
    poetry = Factory().create_poetry(project("module1"))

    builder = SdistBuilder(poetry)
    builder.build()

    sdist = fixtures_dir / "module1" / "dist" / "module1-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        for tarinfo in tar.getmembers():
            assert tarinfo.mtime == 1727883000


def test_sdist_mtime_set_from_envvar_not_int(
    monkeypatch: MonkeyPatch, caplog: LogCaptureFixture
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "october")
    poetry = Factory().create_poetry(project("module1"))

    builder = SdistBuilder(poetry)
    builder.build()

    sdist = fixtures_dir / "module1" / "dist" / "module1-0.1.tar.gz"

    assert sdist.exists()

    assert (
        "SOURCE_DATE_EPOCH environment variable is not an int, using mtime=0"
    ) in caplog.messages
