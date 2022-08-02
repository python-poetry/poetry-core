from __future__ import annotations

import ast
import gzip
import hashlib
import shutil
import tarfile

from email.parser import Parser
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Iterator

import pytest

from poetry.core.factory import Factory
from poetry.core.masonry.builders.sdist import SdistBuilder
from poetry.core.masonry.utils.package_include import PackageInclude
from poetry.core.packages.dependency import Dependency
from poetry.core.packages.project_package import ProjectPackage
from poetry.core.packages.vcs_dependency import VCSDependency


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
    package.extras = {"bar": [Dependency("A", "*")]}

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

    package.extras = {"baz": [Dependency("D", "*")]}

    result = SdistBuilder.convert_dependencies(
        package,
        [Dependency("A", ">=1.2", optional=True), Dependency("B", "~1.0"), c, d],
    )
    main = ["B>=1.0,<1.1"]

    extra_python = (
        ':python_version >= "2.7" and python_version < "2.8" '
        'or python_version >= "3.6" and python_version < "4.0"'
    )
    extra_d_dependency = (
        'baz:python_version >= "2.7" and python_version < "2.8" '
        'or python_version >= "3.4" and python_version < "4.0"'
    )
    extras = {extra_python: ["C==1.2.3"], extra_d_dependency: ["D==3.4.5"]}

    assert result == (main, extras)


def test_make_setup() -> None:
    poetry = Factory().create_poetry(project("complete"))

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
            "extra-script = my_package.extra:main[time]",
            "my-2nd-script = my_package:main2",
            "my-script = my_package:main",
        ]
    }
    assert ns["scripts"] == [str(Path("bin") / "script.sh")]
    assert ns["extras_require"] == {
        'time:python_version ~= "2.7" and sys_platform == "win32" or python_version in "3.4 3.5"': [
            "pendulum>=1.4,<2.0"
        ]
    }


def test_make_pkg_info(mocker: MockerFixture) -> None:
    get_metadata_content = mocker.patch(
        "poetry.core.masonry.builders.builder.Builder.get_metadata_content"
    )
    poetry = Factory().create_poetry(project("complete"))

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


def test_find_files_to_add() -> None:
    poetry = Factory().create_poetry(project("complete"))

    builder = SdistBuilder(poetry)
    result = [f.relative_to_source_root() for f in builder.find_files_to_add()]

    assert sorted(result) == sorted(
        [
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
        ]
    )


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
        'pendulum (>=1.5,<2.0); python_version < "3.4"',
        'pendulum (>=2.0,<3.0); python_version >= "3.4" and python_version < "4.0"',
    ]


def test_find_packages() -> None:
    poetry = Factory().create_poetry(project("complete"))

    builder = SdistBuilder(poetry)

    base = project("complete")
    include = PackageInclude(base, "my_package")

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
    include = PackageInclude(base, "package_src", source="src")

    pkg_dir, packages, pkg_data = builder.find_packages(include)

    assert pkg_dir == str(base / "src")
    assert packages == ["package_src"]
    assert pkg_data == {"": ["*"]}


def test_package() -> None:
    poetry = Factory().create_poetry(project("complete"))

    builder = SdistBuilder(poetry)
    builder.build()

    sdist = fixtures_dir / "complete" / "dist" / "my-package-1.2.3.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "my-package-1.2.3/LICENSE" in tar.getnames()


def test_sdist_reproducibility() -> None:
    poetry = Factory().create_poetry(project("complete"))

    hashes = set()

    for _ in range(2):
        builder = SdistBuilder(poetry)
        builder.build()

        sdist = fixtures_dir / "complete" / "dist" / "my-package-1.2.3.tar.gz"

        assert sdist.exists()

        hashes.add(hashlib.sha256(sdist.read_bytes()).hexdigest())

    assert len(hashes) == 1


def test_setup_py_context() -> None:
    poetry = Factory().create_poetry(project("complete"))

    builder = SdistBuilder(poetry)

    project_setup_py = poetry.file.parent / "setup.py"

    assert not project_setup_py.exists()

    try:
        with builder.setup_py() as setup:
            assert setup.exists()
            assert project_setup_py == setup

            with open(str(setup), "rb") as f:
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

    sdist = fixtures_dir / "source_file" / "dist" / "module-src-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "module-src-0.1/src/module_src.py" in tar.getnames()


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

    sdist = fixtures_dir / "source_package" / "dist" / "package-src-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "package-src-0.1/src/package_src/__init__.py" in tar.getnames()
        assert "package-src-0.1/src/package_src/module.py" in tar.getnames()


def test_default_with_excluded_data(mocker: MockerFixture) -> None:
    # Patch git module to return specific excluded files
    p = mocker.patch("poetry.core.vcs.git.Git.get_ignored_files")
    p.return_value = [
        (
            (
                Path(__file__).parent
                / "fixtures"
                / "default_with_excluded_data"
                / "my_package"
                / "data"
                / "sub_data"
                / "data2.txt"
            )
            .relative_to(project("default_with_excluded_data"))
            .as_posix()
        )
    ]
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
        fixtures_dir / "default_with_excluded_data" / "dist" / "my-package-1.2.3.tar.gz"
    )

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        names = tar.getnames()
        assert len(names) == len(set(names))
        assert "my-package-1.2.3/LICENSE" in names
        assert "my-package-1.2.3/README.rst" in names
        assert "my-package-1.2.3/my_package/__init__.py" in names
        assert "my-package-1.2.3/my_package/data/data1.txt" in names
        assert "my-package-1.2.3/pyproject.toml" in names
        assert "my-package-1.2.3/setup.py" in names
        assert "my-package-1.2.3/PKG-INFO" in names
        # all last modified times should be set to a valid timestamp
        for tarinfo in tar.getmembers():
            if tarinfo.name in [
                "my-package-1.2.3/setup.py",
                "my-package-1.2.3/PKG-INFO",
            ]:
                # generated files have timestamp set to 0
                assert tarinfo.mtime == 0
                continue
            assert tarinfo.mtime > 0


def test_src_excluded_nested_data() -> None:
    module_path = fixtures_dir / "exclude_nested_data_toml"
    poetry = Factory().create_poetry(module_path)

    builder = SdistBuilder(poetry)
    builder.build()

    sdist = module_path / "dist" / "my-package-1.2.3.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        names = tar.getnames()
        assert len(names) == len(set(names))
        assert "my-package-1.2.3/LICENSE" in names
        assert "my-package-1.2.3/README.rst" in names
        assert "my-package-1.2.3/pyproject.toml" in names
        assert "my-package-1.2.3/setup.py" in names
        assert "my-package-1.2.3/PKG-INFO" in names
        assert "my-package-1.2.3/my_package/__init__.py" in names
        assert "my-package-1.2.3/my_package/data/sub_data/data2.txt" not in names
        assert "my-package-1.2.3/my_package/data/sub_data/data3.txt" not in names
        assert "my-package-1.2.3/my_package/data/data1.txt" not in names
        assert "my-package-1.2.3/my_package/data/data2.txt" in names
        assert "my-package-1.2.3/my_package/puplic/publicdata.txt" in names
        assert "my-package-1.2.3/my_package/public/item1/itemdata1.txt" not in names
        assert (
            "my-package-1.2.3/my_package/public/item1/subitem/subitemdata.txt"
            not in names
        )
        assert "my-package-1.2.3/my_package/public/item2/itemdata2.txt" not in names


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


def test_includes() -> None:
    poetry = Factory().create_poetry(project("with-include"))

    builder = SdistBuilder(poetry)

    builder.build()

    sdist = fixtures_dir / "with-include" / "dist" / "with-include-1.2.3.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "with-include-1.2.3/extra_dir/vcs_excluded.txt" in tar.getnames()
        assert "with-include-1.2.3/notes.txt" in tar.getnames()


def test_includes_with_inline_table() -> None:
    poetry = Factory().create_poetry(project("with_include_inline_table"))

    builder = SdistBuilder(poetry)

    builder.build()

    sdist = (
        fixtures_dir
        / "with_include_inline_table"
        / "dist"
        / "with-include-1.2.3.tar.gz"
    )

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "with-include-1.2.3/both.txt" in tar.getnames()
        assert "with-include-1.2.3/wheel_only.txt" not in tar.getnames()
        assert "with-include-1.2.3/tests/__init__.py" in tar.getnames()
        assert "with-include-1.2.3/tests/test_foo/test.py" in tar.getnames()


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

    sdist = root / "dist" / "pep-561-stubs-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        names = tar.getnames()
        assert "pep-561-stubs-0.1/pkg-stubs/__init__.pyi" in names
        assert "pep-561-stubs-0.1/pkg-stubs/module.pyi" in names
        assert "pep-561-stubs-0.1/pkg-stubs/subpkg/__init__.pyi" in names


def test_sdist_disable_setup_py() -> None:
    module_path = fixtures_dir / "disable_setup_py"
    poetry = Factory().create_poetry(module_path)

    builder = SdistBuilder(poetry)
    builder.build()

    sdist = module_path / "dist" / "my-package-1.2.3.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert set(tar.getnames()) == {
            "my-package-1.2.3/README.rst",
            "my-package-1.2.3/pyproject.toml",
            "my-package-1.2.3/PKG-INFO",
            "my-package-1.2.3/my_package/__init__.py",
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
