from __future__ import annotations

import shutil

from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import cast

import pytest

from packaging.utils import canonicalize_name

from poetry.core.constraints.version import parse_constraint
from poetry.core.factory import Factory
from poetry.core.packages.dependency import Dependency
from poetry.core.packages.dependency_group import MAIN_GROUP
from poetry.core.packages.directory_dependency import DirectoryDependency
from poetry.core.packages.file_dependency import FileDependency
from poetry.core.packages.url_dependency import URLDependency
from poetry.core.packages.vcs_dependency import VCSDependency
from poetry.core.pyproject.tables import BuildSystem
from poetry.core.utils._compat import tomllib
from poetry.core.version.markers import SingleMarker


if TYPE_CHECKING:
    from pytest import LogCaptureFixture


fixtures_dir = Path(__file__).parent / "fixtures"


@pytest.fixture
def complete_legacy_warnings() -> list[str]:
    return [
        "[tool.poetry.name] is deprecated. Use [project.name] instead.",
        (
            "[tool.poetry.version] is set but 'version' is not in "
            "[project.dynamic]. If it is static use [project.version]. If it "
            "is dynamic, add 'version' to [project.dynamic].\n"
            "If you want to set the version dynamically via `poetry build "
            "--local-version` or you are using a plugin, which sets the "
            "version dynamically, you should define the version in "
            "[tool.poetry] and add 'version' to [project.dynamic]."
        ),
        "[tool.poetry.description] is deprecated. Use [project.description] instead.",
        (
            "[tool.poetry.readme] is set but 'readme' is not in "
            "[project.dynamic]. If it is static use [project.readme]. If it "
            "is dynamic, add 'readme' to [project.dynamic].\n"
            "If you want to define multiple readmes, you should define them "
            "in [tool.poetry] and add 'readme' to [project.dynamic]."
        ),
        "[tool.poetry.license] is deprecated. Use [project.license] instead.",
        "[tool.poetry.authors] is deprecated. Use [project.authors] instead.",
        "[tool.poetry.maintainers] is deprecated. Use [project.maintainers] instead.",
        "[tool.poetry.keywords] is deprecated. Use [project.keywords] instead.",
        (
            "[tool.poetry.classifiers] is set but 'classifiers' is not in "
            "[project.dynamic]. If it is static use [project.classifiers]. If it "
            "is dynamic, add 'classifiers' to [project.dynamic].\n"
            "ATTENTION: Per default Poetry determines classifiers for "
            "supported Python versions and license automatically. If you "
            "define classifiers in [project], you disable the automatic "
            "enrichment. In other words, you have to define all classifiers "
            "manually. If you want to use Poetry's automatic enrichment of "
            "classifiers, you should define them in [tool.poetry] and add "
            "'classifiers' to [project.dynamic]."
        ),
        "[tool.poetry.homepage] is deprecated. Use [project.urls] instead.",
        "[tool.poetry.repository] is deprecated. Use [project.urls] instead.",
        "[tool.poetry.documentation] is deprecated. Use [project.urls] instead.",
        "[tool.poetry.plugins] is deprecated. Use [project.entry-points] instead.",
        (
            "[tool.poetry.extras] is deprecated. Use "
            "[project.optional-dependencies] instead."
        ),
        (
            "Defining console scripts in [tool.poetry.scripts] is deprecated. "
            "Use [project.scripts] instead. "
            "([tool.poetry.scripts] should only be used for scripts of type 'file')."
        ),
    ]


@pytest.fixture
def complete_legacy_duplicate_warnings() -> list[str]:
    return [
        (
            "[project.name] and [tool.poetry.name] are both set. The latter "
            "will be ignored."
        ),
        (
            "[project.version] and [tool.poetry.version] are both set. The "
            "latter will be ignored.\n"
            "If you want to set the version dynamically via `poetry build "
            "--local-version` or you are using a plugin, which sets the "
            "version dynamically, you should define the version in "
            "[tool.poetry] and add 'version' to [project.dynamic]."
        ),
        (
            "[project.description] and [tool.poetry.description] are both "
            "set. The latter will be ignored."
        ),
        (
            "[project.readme] and [tool.poetry.readme] are both set. The "
            "latter will be ignored.\n"
            "If you want to define multiple readmes, you should define them "
            "in [tool.poetry] and add 'readme' to [project.dynamic]."
        ),
        (
            "[project.license] and [tool.poetry.license] are both set. The "
            "latter will be ignored."
        ),
        (
            "[project.authors] and [tool.poetry.authors] are both set. The "
            "latter will be ignored."
        ),
        (
            "[project.maintainers] and [tool.poetry.maintainers] are both "
            "set. The latter will be ignored."
        ),
        (
            "[project.keywords] and [tool.poetry.keywords] are both set. The "
            "latter will be ignored."
        ),
        (
            "[project.classifiers] and [tool.poetry.classifiers] are both "
            "set. The latter will be ignored.\n"
            "ATTENTION: Per default Poetry determines classifiers for "
            "supported Python versions and license automatically. If you "
            "define classifiers in [project], you disable the automatic "
            "enrichment. In other words, you have to define all classifiers "
            "manually. If you want to use Poetry's automatic enrichment of "
            "classifiers, you should define them in [tool.poetry] and add "
            "'classifiers' to [project.dynamic]."
        ),
        (
            "[project.urls] and [tool.poetry.homepage] are both set. The "
            "latter will be ignored."
        ),
        (
            "[project.urls] and [tool.poetry.repository] are both set. The "
            "latter will be ignored."
        ),
        (
            "[project.urls] and [tool.poetry.documentation] are both set. "
            "The latter will be ignored."
        ),
        (
            "[project.entry-points] and [tool.poetry.plugins] are both set. The "
            "latter will be ignored."
        ),
        (
            "[project.optional-dependencies] and [tool.poetry.extras] are "
            "both set. The latter will be ignored."
        ),
        (
            "[project.scripts] is set and there are console scripts "
            "in [tool.poetry.scripts]. The latter will be ignored."
        ),
    ]


@pytest.mark.parametrize(
    "project", ["sample_project", "sample_project_new", "sample_project_dynamic"]
)
def test_create_poetry(project: str) -> None:
    new_format = project == "sample_project_new"
    dynamic = project == "sample_project_dynamic"
    poetry = Factory().create_poetry(fixtures_dir / project)

    assert poetry.is_package_mode

    package = poetry.package

    assert package.name == "my-package"
    assert package.version.text == "1.2.3"
    assert package.description == "Some description."
    assert package.authors == ["Sébastien Eustace <sebastien@eustace.io>"]
    assert package.maintainers == ["Sébastien Eustace <sebastien@eustace.io>"]
    if new_format:
        assert package.license is None
        assert package.license_expression == "MIT"
    else:
        assert package.license is not None
        assert package.license.id == "MIT"
        assert package.license_expression is None
    assert (
        package.readmes[0].relative_to(fixtures_dir).as_posix()
        == f"{project}/README.rst"
    )
    assert package.homepage == "https://python-poetry.org"
    assert package.repository_url == "https://github.com/python-poetry/poetry"
    assert package.keywords == ["packaging", "dependency", "poetry"]

    assert package.python_versions == ">=3.6"
    assert str(package.python_constraint) == ">=3.6"

    dependencies: dict[str, Dependency] = {}
    for dep in package.requires:
        dependencies[dep.name] = dep

    cleo = dependencies["cleo"]
    assert cleo.pretty_constraint == (">=0.6,<1.0" if new_format else "^0.6")
    assert not cleo.is_optional()

    pendulum = dependencies["pendulum"]
    assert pendulum.pretty_constraint == ("rev 2.0" if new_format else "branch 2.0")
    assert pendulum.is_vcs()
    pendulum = cast("VCSDependency", pendulum)
    assert pendulum.vcs == "git"
    assert pendulum.rev == "2.0" if new_format else pendulum.branch == "2.0"
    assert pendulum.source == "https://github.com/sdispater/pendulum.git"
    assert pendulum.allows_prereleases()
    assert not pendulum.develop

    tomlkit = dependencies["tomlkit"]
    assert tomlkit.pretty_constraint == "rev 3bff550"
    assert tomlkit.is_vcs()
    tomlkit = cast("VCSDependency", tomlkit)
    assert tomlkit.vcs == "git"
    assert tomlkit.rev == "3bff550"
    assert tomlkit.source == "https://github.com/sdispater/tomlkit.git"
    assert tomlkit.allows_prereleases()
    assert not tomlkit.develop if new_format else tomlkit.develop
    tomlkit_for_locking = next(d for d in package.all_requires if d.name == "tomlkit")
    assert isinstance(tomlkit_for_locking, VCSDependency)
    assert tomlkit_for_locking.develop

    requests = dependencies["requests"]
    assert requests.pretty_constraint == (
        ">=2.18,<3.0" if new_format or dynamic else "^2.18"
    )
    assert not requests.is_vcs()
    assert requests.allows_prereleases() is None
    assert requests.is_optional()
    assert requests.extras == frozenset({"security"})

    pathlib2 = dependencies["pathlib2"]
    assert pathlib2.pretty_constraint == (">=2.2,<3.0" if new_format else "^2.2")
    assert pathlib2.python_versions in {"~2.7", ">=2.7 <2.8"}
    assert not pathlib2.is_optional()

    demo = dependencies["demo"]
    assert demo.is_file()
    assert not demo.is_vcs()
    assert demo.name == "demo"
    assert demo.pretty_constraint == "*"

    demo = dependencies["my-package"]
    assert not demo.is_file()
    assert demo.is_directory()
    assert not demo.is_vcs()
    assert demo.name == "my-package"
    assert demo.pretty_constraint == "*"

    simple_project = dependencies["simple-project"]
    assert not simple_project.is_file()
    assert simple_project.is_directory()
    assert not simple_project.is_vcs()
    assert simple_project.name == "simple-project"
    assert simple_project.pretty_constraint == "*"

    functools32 = dependencies["functools32"]
    assert functools32.name == "functools32"
    assert functools32.pretty_constraint == (
        ">=3.2.3,<3.3.0" if new_format else "^3.2.3"
    )
    assert (
        str(functools32.marker)
        == 'python_version ~= "2.7" and sys_platform == "win32" or python_version in'
        ' "3.4 3.5"'
    )

    dataclasses = dependencies["dataclasses"]
    assert dataclasses.name == "dataclasses"
    assert dataclasses.pretty_constraint == (">=0.7,<1.0" if new_format else "^0.7")
    assert dataclasses.python_versions == ">=3.6.1 <3.7"
    assert (
        str(dataclasses.marker)
        == 'python_full_version >= "3.6.1" and python_version < "3.7"'
    )

    assert "db" in package.extras

    classifiers = package.classifiers

    assert classifiers == [
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]

    if new_format:
        assert package.all_classifiers == package.classifiers
    else:
        assert package.all_classifiers == [
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Programming Language :: Python :: 3.13",
            "Programming Language :: Python :: 3.14",
            "Topic :: Software Development :: Build Tools",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ]


@pytest.mark.parametrize(
    "project", ["sample_project_with_groups", "sample_project_with_groups_new"]
)
def test_create_poetry_with_groups(project: str) -> None:
    poetry = Factory().create_poetry(fixtures_dir / project)

    assert "docs" in poetry.package._dependency_groups
    assert "test" in poetry.package._dependency_groups
    assert poetry.package._dependency_groups["docs"].is_optional()  # type: ignore[index]
    assert not poetry.package._dependency_groups["test"].is_optional()  # type: ignore[index]

    package = poetry.package

    expected_dependencies = {
        "test": ["pytest", "coverage"],
        "dev": ["pre-commit", "pytest", "coverage"],
        "docs": ["mkdocs"],
        "all": ["pytest", "coverage", "pre-commit", "pytest", "coverage", "mkdocs"],
    }

    dependencies = defaultdict(list)
    for dep in package.all_requires:
        assert len(dep.groups) == 1
        for group in dep.groups:
            if group != MAIN_GROUP:
                dependencies[group].append(dep.name)

    assert dependencies == expected_dependencies

    for dep in package.all_requires:
        if dep.name == "mkdocs":
            assert isinstance(dep, VCSDependency)
            # The "develop" flag of mkdocs from tool.poetry
            # must also be set for the all extra!
            assert dep.develop is True
            assert dep.source_type == "git"
            assert dep.source == "https://github.com/mkdocs/mkdocs.git"


def test_create_poetry_with_dependencies_with_subdirectory() -> None:
    poetry = Factory().create_poetry(
        fixtures_dir / "project_with_dependencies_with_subdirectory"
    )
    package = poetry.package
    dependencies = {str(dep.name): dep for dep in package.requires}

    # git dependency
    pendulum = dependencies["pendulum"]
    assert pendulum.is_vcs()
    assert pendulum.pretty_constraint == "branch 2.0"
    pendulum = cast("VCSDependency", pendulum)
    assert pendulum.source == "https://github.com/sdispater/pendulum.git"
    assert pendulum.directory == "sub"

    # file dependency
    demo = dependencies["demo"]
    assert demo.is_file()
    assert demo.pretty_constraint == "*"
    demo = cast("FileDependency", demo)
    assert demo.path == Path("../distributions/demo-0.1.0-in-subdir.zip")
    assert demo.directory == "sub"
    demo_dependencies = [dep for dep in package.requires if dep.name == "demo"]
    assert len(demo_dependencies) == 2
    assert demo_dependencies[0] == demo_dependencies[1]
    assert {str(dep.marker) for dep in demo_dependencies} == {
        'sys_platform == "win32"',
        'sys_platform == "linux"',
    }

    # directory dependency
    simple_project = dependencies["simple-project"]
    assert simple_project.is_directory()
    assert simple_project.pretty_constraint == "*"
    simple_project = cast("DirectoryDependency", simple_project)
    assert simple_project.path == Path("../simple_project")
    with pytest.raises(AttributeError):
        _ = simple_project.directory  # type: ignore[attr-defined]

    # url dependency
    foo = dependencies["foo"]
    assert foo.is_url()
    assert foo.pretty_constraint == "*"
    foo = cast("URLDependency", foo)
    assert foo.url == "https://example.com/foo.zip"
    assert foo.directory == "sub"


def test_create_poetry_with_packages_and_includes() -> None:
    poetry = Factory().create_poetry(
        fixtures_dir.parent / "masonry" / "builders" / "fixtures" / "with-include"
    )

    package = poetry.package

    assert package.packages == [
        {"include": "extra_dir/**/*.py", "format": ["sdist", "wheel"]},
        {"include": "extra_dir/**/*.py", "format": ["sdist", "wheel"]},
        {"include": "my_module.py", "format": ["sdist", "wheel"]},
        {"include": "package_with_include", "format": ["sdist", "wheel"]},
        {"include": "tests", "format": ["sdist"]},
        {"include": "for_wheel_only", "format": ["wheel"]},
        {"include": "src_package", "from": "src", "format": ["sdist", "wheel"]},
        {
            "include": "from_to",
            "from": "etc",
            "to": "target_from_to",
            "format": ["sdist", "wheel"],
        },
        {
            "include": "my_module_to.py",
            "to": "target_module",
            "format": ["sdist", "wheel"],
        },
    ]

    assert package.include == [
        {"path": "extra_dir/vcs_excluded.py", "format": ["sdist", "wheel"]},
        {"path": "notes.txt", "format": ["sdist"]},
    ]


def test_create_poetry_with_multi_constraints_dependency() -> None:
    poetry = Factory().create_poetry(
        fixtures_dir / "project_with_multi_constraints_dependency"
    )

    package = poetry.package

    assert len(package.requires) == 2


def test_create_poetry_non_package_mode() -> None:
    poetry = Factory().create_poetry(fixtures_dir / "non_package_mode")

    assert not poetry.is_package_mode


@pytest.mark.parametrize(
    "project", ["none", "file", "text", "text_spdx", "str", "str_empty", "str_no_spdx"]
)
@pytest.mark.parametrize("with_license_files", [False, True, "empty"])
def test_create_poetry_with_license_type(
    project: str, with_license_files: bool | str, tmp_path: Path
) -> None:
    project_dir = fixtures_dir / f"with_license_type_{project}"
    expected_license_files: tuple[str, ...] | Path | None = None
    if with_license_files:
        if with_license_files == "empty":
            content = ""
            expected_license_files = ()
        else:
            content = '"LICEN[CS]E*", "AUTHORS*"'
            expected_license_files = ("LICEN[CS]E*", "AUTHORS*")

        orig_project_dir = project_dir
        project_dir = tmp_path / project
        shutil.copytree(orig_project_dir, project_dir)
        pyproject_file = project_dir / "pyproject.toml"
        new_lines = []
        for line in pyproject_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("keywords = "):
                new_lines.append(f"license-files = [{content}]")
            new_lines.append(line)
        pyproject_file.write_text("\n".join(new_lines), encoding="utf-8")

    license_type = project.split("_", 1)[0]
    expected_license_id: str | None = None
    expected_license_expression: str | None = None
    if license_type == "none":
        pass
    elif license_type == "file":
        expected_license_id = (project_dir / "LICENSE").read_text(encoding="utf-8")
        expected_license_files = Path("LICENSE")
    elif license_type in {"str", "text"}:
        with (project_dir / "pyproject.toml").open("rb") as f:
            data = tomllib.load(f)
        project_license = data["project"]["license"]
        if license_type == "text":
            expected_license_id = project_license["text"]
        elif project == "str_no_spdx":
            expected_license_id = project_license
        elif project == "str":
            expected_license_expression = project_license
    else:
        raise RuntimeError("unexpected license type")

    if with_license_files and license_type in {"file", "text"}:
        with pytest.raises(ValueError) as e:
            Factory().create_poetry(project_dir)
        assert str(e.value) == (
            "[project.license] must be of type string"
            " if [project.license-files] is defined."
        )
    else:
        poetry = Factory().create_poetry(project_dir)

        if expected_license_id is None:
            assert poetry.package.license is None
        else:
            assert poetry.package.license is not None
            assert poetry.package.license.id == expected_license_id
        assert poetry.package.license_expression == expected_license_expression
        assert poetry.package.license_files == expected_license_files


@pytest.mark.parametrize(
    ("invalid_glob", "expected_message"),
    [
        (
            r"sub\\LICENSE",
            (
                "Invalid entry in [project.license-files]: 'sub\\LICENSE'"
                " (Path delimiters must be forward slashes.)"
            ),
        ),
        (
            "../LICENSE",
            (
                "Invalid entry in [project.license-files]: '../LICENSE'"
                " ('..' must not be used.)"
            ),
        ),
        (
            "./../LICENSE",
            (
                "Invalid entry in [project.license-files]: './../LICENSE'"
                " ('..' must not be used.)"
            ),
        ),
        (
            "sub/../../LICENSE",
            (
                "Invalid entry in [project.license-files]: 'sub/../../LICENSE'"
                " ('..' must not be used.)"
            ),
        ),
    ],
)
def test_create_poetry_with_invalid_license_files_glob(
    tmp_path: Path, invalid_glob: str, expected_message: str
) -> None:
    project_file = tmp_path / "pyproject.toml"
    project_file.write_text(
        f"""\
[project]
name = "foo"
version = "1"
license-files = [
    "LICENSE",
    "{invalid_glob}",
    "licenses/**",
]
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError) as e:
        Factory().create_poetry(tmp_path)
    assert str(e.value) == expected_message


def test_create_poetry_fails_with_missing_license_file() -> None:
    project_dir = fixtures_dir / "missing_license_file"
    with pytest.raises(FileNotFoundError) as e:
        Factory().create_poetry(project_dir)

    assert str((project_dir / "LICENSE").absolute()) in str(e.value)


@pytest.mark.parametrize(
    ("requires_python", "python", "expected_versions", "expected_constraint"),
    [
        (">=3.8", None, ">=3.8", ">=3.8"),
        (None, "^3.8", "^3.8", ">=3.8,<4.0"),
        (">=3.8", "^3.8", "^3.8", ">=3.8,<4.0"),
    ],
)
def test_create_poetry_python_version(
    requires_python: str,
    python: str,
    expected_versions: str,
    expected_constraint: str,
    tmp_path: Path,
) -> None:
    content = '[project]\nname = "foo"\nversion = "1"\n'
    if requires_python:
        content += f'requires-python = "{requires_python}"\n'
    if python:
        content += f'[tool.poetry.dependencies]\npython = "{python}"\n'
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
    poetry = Factory().create_poetry(tmp_path)

    package = poetry.package
    assert package.requires_python == requires_python or python
    assert package.python_versions == expected_versions
    assert str(package.python_constraint) == expected_constraint


def test_create_poetry_python_version_not_compatible(tmp_path: Path) -> None:
    content = """
[project]
name = "foo"
version = "1"
requires-python = ">=3.8"

[tool.poetry.dependencies]
python = ">=3.7"
"""
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
    with pytest.raises(ValueError) as e:
        Factory().create_poetry(tmp_path)

    assert "not a subset" in str(e.value)


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (  # static
            """\
[project]
name = "foo"
version = "1"
requires-python = "3.10"
classifiers = ["License :: OSI Approved :: MIT License"]
""",
            ["License :: OSI Approved :: MIT License"],
        ),
        (  # dynamic
            """\
[project]
name = "foo"
version = "1"
requires-python = "3.10"
dynamic = [ "classifiers" ]

[tool.poetry]
classifiers = ["License :: OSI Approved :: MIT License"]
""",
            [
                "License :: OSI Approved :: MIT License",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3.10",
            ],
        ),
        (  # legacy
            """\
[tool.poetry]
name = "foo"
version = "1"
classifiers = ["License :: OSI Approved :: MIT License"]

[tool.poetry.dependencies]
python = "~3.10"
""",
            [
                "License :: OSI Approved :: MIT License",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3.10",
            ],
        ),
    ],
)
def test_create_poetry_classifiers(
    content: str, expected: list[str], tmp_path: Path
) -> None:
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
    poetry = Factory().create_poetry(tmp_path)

    assert poetry.package.all_classifiers == expected


def test_create_poetry_no_readme(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.poetry]\nname="foo"\nversion="1"\nauthors = []\ndescription = ""\n',
        encoding="utf-8",
    )
    poetry = Factory().create_poetry(tmp_path)

    assert not poetry.package.readmes


def test_create_poetry_empty_readme(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.poetry]\nname="foo"\nversion="1"\nauthors = []\ndescription = ""\n'
        'readme = ""\n',
        encoding="utf-8",
    )
    poetry = Factory().create_poetry(tmp_path)

    assert not poetry.package.readmes


def test_validate() -> None:
    complete = fixtures_dir / "complete.toml"
    with complete.open("rb") as f:
        content = tomllib.load(f)

    assert Factory.validate(content) == {"errors": [], "warnings": []}


def test_validate_strict_legacy_warnings(complete_legacy_warnings: list[str]) -> None:
    complete = fixtures_dir / "complete.toml"
    with complete.open("rb") as f:
        content = tomllib.load(f)

    assert Factory.validate(content, strict=True) == {
        "errors": [],
        "warnings": complete_legacy_warnings,
    }


def test_validate_strict_legacy_duplicate_warnings(
    complete_legacy_duplicate_warnings: list[str],
) -> None:
    complete = fixtures_dir / "complete_duplicates.toml"
    with complete.open("rb") as f:
        content = tomllib.load(f)

    assert Factory.validate(content, strict=True) == {
        "errors": [],
        "warnings": complete_legacy_duplicate_warnings,
    }


def test_validate_strict_new_no_warnings() -> None:
    complete = fixtures_dir / "complete_new.toml"
    with complete.open("rb") as f:
        content = tomllib.load(f)

    assert Factory.validate(content, strict=True) == {"errors": [], "warnings": []}


def test_validate_strict_dynamic_warnings() -> None:
    # some fields are allowed to be dynamic, but some are not
    complete = fixtures_dir / "complete_new_dynamic_invalid.toml"
    with complete.open("rb") as f:
        content = tomllib.load(f)

    assert Factory.validate(content, strict=True) == {
        "errors": ["project must contain ['name'] properties"],
        "warnings": [
            # version, readme and classifiers are allowed to be dynamic!
            "[tool.poetry.name] is deprecated. Use [project.name] instead.",
            (
                "[tool.poetry.description] is deprecated. Use "
                "[project.description] instead."
            ),
            "[tool.poetry.license] is deprecated. Use [project.license] instead.",
            "[tool.poetry.authors] is deprecated. Use [project.authors] instead.",
            (
                "[tool.poetry.maintainers] is deprecated. Use "
                "[project.maintainers] instead."
            ),
            "[tool.poetry.keywords] is deprecated. Use [project.keywords] instead.",
            "[tool.poetry.homepage] is deprecated. Use [project.urls] instead.",
            "[tool.poetry.repository] is deprecated. Use [project.urls] instead.",
            "[tool.poetry.documentation] is deprecated. Use [project.urls] instead.",
            (
                "[tool.poetry.extras] is deprecated. Use "
                "[project.optional-dependencies] instead."
            ),
            (
                "Defining console scripts in [tool.poetry.scripts] is deprecated. "
                "Use [project.scripts] instead. "
                "([tool.poetry.scripts] should only be used for scripts of type 'file')."
            ),
        ],
    }


def test_validate_local_version(tmp_path: Path) -> None:
    project = tmp_path / "local_version.toml"
    project.write_text(
        """[project]\nname = "local-version"\nversion = "0.5.0+LOCAL.123A"\n""",
        encoding="utf-8",
    )
    with project.open("rb") as f:
        content = tomllib.load(f)

    assert Factory.validate(content) == {"errors": [], "warnings": []}


def test_validate_fails() -> None:
    complete = fixtures_dir / "complete.toml"
    with complete.open("rb") as f:
        content = tomllib.load(f)
    content["tool"]["poetry"]["authors"] = "this is not a valid array"

    expected = "tool.poetry.authors must be array"

    assert Factory.validate(content) == {"errors": [expected], "warnings": []}


def test_validate_without_strict_fails_only_non_strict() -> None:
    project_failing_strict_validation = (
        fixtures_dir / "project_failing_strict_validation" / "pyproject.toml"
    )
    with project_failing_strict_validation.open("rb") as f:
        content = tomllib.load(f)

    assert Factory.validate(content) == {
        "errors": [
            "Either [project.name] or [tool.poetry.name] is required in package mode.",
            (
                "Either [project.version] or [tool.poetry.version] is required in "
                "package mode."
            ),
        ],
        "warnings": [],
    }


def test_validate_strict_fails_strict_and_non_strict() -> None:
    project_failing_strict_validation = (
        fixtures_dir / "project_failing_strict_validation" / "pyproject.toml"
    )
    with project_failing_strict_validation.open("rb") as f:
        content = tomllib.load(f)

    assert Factory.validate(content, strict=True) == {
        "errors": [
            "Either [project.name] or [tool.poetry.name] is required in package mode.",
            (
                "Either [project.version] or [tool.poetry.version] is required in "
                "package mode."
            ),
            (
                'Cannot find dependency "missing_extra" for extra "some-extras" in '
                "main dependencies."
            ),
            (
                'Cannot find dependency "another_missing_extra" for extra '
                '"some-extras" in main dependencies.'
            ),
            (
                'The script "a_script_with_unknown_extra" requires extra "foo" which is'
                " not defined."
            ),
            (
                "Declared README files must be of same type: found text/markdown,"
                " text/x-rst"
            ),
        ],
        "warnings": [
            (
                "[tool.poetry.readme] is set but 'readme' is not in "
                "[project.dynamic]. If it is static use [project.readme]. If it "
                "is dynamic, add 'readme' to [project.dynamic].\n"
                "If you want to define multiple readmes, you should define them "
                "in [tool.poetry] and add 'readme' to [project.dynamic]."
            ),
            (
                "[tool.poetry.extras] is deprecated. Use "
                "[project.optional-dependencies] instead."
            ),
            (
                "Defining console scripts in [tool.poetry.scripts] is deprecated. "
                "Use [project.scripts] instead. "
                "([tool.poetry.scripts] should only be used for scripts of type 'file')."
            ),
            (
                "A wildcard Python dependency is ambiguous. Consider specifying a more"
                " explicit one."
            ),
            (
                'The "pathlib2" dependency specifies the "allows-prereleases" property,'
                ' which is deprecated. Use "allow-prereleases" instead.'
            ),
            (
                'The script "a_script_with_unknown_extra" depends on an extra. Scripts'
                " depending on extras are deprecated and support for them will be"
                " removed in a future version of poetry/poetry-core. See"
                " https://packaging.python.org/en/latest/specifications/entry-points/#data-model"
                " for details."
            ),
        ],
    }


@pytest.mark.parametrize("with_project_section", [True, False])
def test_validate_dependencies_non_package_mode(with_project_section: bool) -> None:
    content: dict[str, Any] = {
        "tool": {"poetry": {"package-mode": False, "dependencies": {"foo": "*"}}}
    }
    expected: dict[str, list[str]] = {"errors": [], "warnings": []}
    if with_project_section:
        content["project"] = {"name": "my-project"}
        expected["warnings"] = [
            (
                "[tool.poetry.dependencies] is set but [project.dependencies] is "
                "not and 'dependencies' is not in [project.dynamic]. You should "
                "either migrate [tool.poetry.dependencies] to "
                "[project.dependencies] (if you do not need Poetry-specific "
                "features) or add [project.dependencies] in addition to "
                "[tool.poetry.dependencies] or add 'dependencies' to "
                "[project.dynamic]."
            )
        ]
    assert Factory.validate(content, strict=True) == expected


@pytest.mark.parametrize("with_project_section", [True, False])
def test_validate_python_non_package_mode(with_project_section: bool) -> None:
    content: dict[str, Any] = {
        "tool": {"poetry": {"package-mode": False, "dependencies": {"python": ">=3.9"}}}
    }
    expected: dict[str, list[str]] = {"errors": [], "warnings": []}
    if with_project_section:
        content["project"] = {"name": "my-project", "dynamic": ["dependencies"]}
        expected["warnings"] = [
            (
                "[tool.poetry.dependencies.python] is set but [project.requires-python]"
                " is not set and 'requires-python' is not in [project.dynamic]."
            )
        ]
    assert Factory.validate(content, strict=True) == expected


@pytest.mark.parametrize("section", ["project", "poetry"])
@pytest.mark.parametrize("with_license_classifier", [True, False])
def test_validate_deprecated_license_classifiers(
    section: str, with_license_classifier: bool
) -> None:
    content: dict[str, Any] = {
        "project": {"name": "my-project", "version": "1.0", "license": "MIT"},
        "tool": {"poetry": {}},
    }
    classifiers = ["Topic :: Software Development :: Libraries :: Python Modules"]

    expected: dict[str, list[str]] = {"errors": [], "warnings": []}
    if with_license_classifier:
        classifiers.append("License :: OSI Approved :: MIT License")
        expected["warnings"].append(
            "License classifiers are deprecated. Use [project.license] instead."
        )

    if section == "project":
        content["project"]["classifiers"] = classifiers
    elif section == "poetry":
        content["tool"]["poetry"]["classifiers"] = classifiers
        content["project"]["dynamic"] = ["classifiers"]
    else:
        raise RuntimeError("unexpected section")

    assert Factory.validate(content, strict=True) == expected


@pytest.mark.parametrize(
    "project", ["none", "file", "text", "text_spdx", "str", "str_empty", "str_no_spdx"]
)
@pytest.mark.parametrize("with_license_files", [False, True])
def test_validate_with_license_type(
    project: str, with_license_files: bool, tmp_path: Path
) -> None:
    project_dir = fixtures_dir / f"with_license_type_{project}"
    pyproject_file = project_dir / "pyproject.toml"
    if with_license_files:
        orig_project_dir = project_dir
        project_dir = tmp_path / project
        shutil.copytree(orig_project_dir, project_dir)
        pyproject_file = project_dir / "pyproject.toml"
        new_lines = []
        for line in pyproject_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("keywords = "):
                new_lines.append('license-files = ["LICEN[CS]E*", "AUTHORS*"]')
            new_lines.append(line)
        pyproject_file.write_text("\n".join(new_lines), encoding="utf-8")

    expected_warnings = []
    if project.split("_", 1)[0] in {"file", "text"}:
        expected_warnings.append(
            "Defining [project.license] as a table is deprecated."
            " [project.license] should be a valid SPDX license expression."
            " License files can be referenced in [project.license-files]."
        )
    elif project in {"str_empty", "str_no_spdx"}:
        expected_warnings.append(
            "[project.license] is not a valid SPDX expression."
            " This is deprecated and will raise an error in the future."
        )

    with pyproject_file.open("rb") as f:
        content = tomllib.load(f)

    assert Factory.validate(content, strict=True) == {
        "errors": [],
        "warnings": expected_warnings,
    }


def test_strict_validation_success_on_multiple_readme_files() -> None:
    with_readme_files = fixtures_dir / "with_readme_files" / "pyproject.toml"
    with with_readme_files.open("rb") as f:
        content = tomllib.load(f)

    assert Factory.validate(content, strict=True) == {"errors": [], "warnings": []}


def test_strict_validation_fails_on_readme_files_with_unmatching_types() -> None:
    with_readme_files = fixtures_dir / "with_readme_files" / "pyproject.toml"
    with with_readme_files.open("rb") as f:
        content = tomllib.load(f)
    content["tool"]["poetry"]["readme"][0] = "README.md"

    assert Factory.validate(content, strict=True) == {
        "errors": [
            "Declared README files must be of same type: found text/markdown,"
            " text/x-rst"
        ],
        "warnings": [],
    }


def test_create_poetry_fails_on_invalid_configuration() -> None:
    with pytest.raises(RuntimeError) as e:
        Factory().create_poetry(
            Path(__file__).parent / "fixtures" / "invalid_pyproject" / "pyproject.toml"
        )

    expected = """\
The Poetry configuration is invalid:
  - Either [project.name] or [tool.poetry.name] is required in package mode.
  - Either [project.version] or [tool.poetry.version] is required in package mode.
"""
    assert str(e.value) == expected


def test_create_poetry_fails_on_invalid_mode() -> None:
    with pytest.raises(RuntimeError) as e:
        Factory().create_poetry(
            Path(__file__).parent / "fixtures" / "invalid_mode" / "pyproject.toml"
        )

    expected = """\
The Poetry configuration is invalid:
  - tool.poetry.package-mode must be boolean
  - Either [project.name] or [tool.poetry.name] is required in package mode.
  - Either [project.version] or [tool.poetry.version] is required in package mode.
"""
    assert str(e.value) == expected


def test_create_poetry_omits_dev_dependencies_iff_with_dev_is_false() -> None:
    poetry = Factory().create_poetry(fixtures_dir / "sample_project", with_groups=False)
    assert not any("dev" in r.groups for r in poetry.package.all_requires)

    poetry = Factory().create_poetry(fixtures_dir / "sample_project")
    assert any("dev" in r.groups for r in poetry.package.all_requires)


def test_create_poetry_with_invalid_dev_dependencies(caplog: LogCaptureFixture) -> None:
    poetry = Factory().create_poetry(
        fixtures_dir / "project_with_invalid_dev_deps", with_groups=False
    )
    assert not any("dev" in r.groups for r in poetry.package.all_requires)

    assert not caplog.records
    poetry = Factory().create_poetry(fixtures_dir / "project_with_invalid_dev_deps")
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "WARNING"
    assert "does not exist" in record.message
    assert any("dev" in r.groups for r in poetry.package.all_requires)


@pytest.mark.parametrize("with_groups", [True, False])
def test_create_poetry_with_invalid_dependency_groups(with_groups: bool) -> None:
    with pytest.raises(RuntimeError) as e:
        _ = Factory().create_poetry(
            fixtures_dir / "project_with_invalid_dependency_groups",
            with_groups=with_groups,
        )

    expected = """\
The Poetry configuration is invalid:
  - dependency-groups.testing[1] must be valid exactly by one definition\
 (0 matches found)
"""
    assert str(e.value) == expected


def test_create_poetry_with_duplicated_dependency_groups() -> None:
    with pytest.raises(RuntimeError) as e:
        _ = Factory().create_poetry(
            fixtures_dir / "project_with_duplicated_dependency_groups",
        )

    assert (
        "Duplicate dependency group name after normalization: test (Test, test)"
        in str(e.value)
    )


def test_create_poetry_with_dependency_groups_missing_include() -> None:
    with pytest.raises(ValueError) as e:
        _ = Factory().create_poetry(
            fixtures_dir / "project_with_dependency_groups_missing_include",
        )

    assert (
        str(e.value) == "Group 'test' includes group 'coverage' which is not defined."
    )


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        (
            "project_with_dependency_groups_simple_cycle",
            [
                "Cyclic dependency group include in test: coverage -> test",
                "Cyclic dependency group include in coverage: test -> coverage",
            ],
        ),
        (
            "project_with_dependency_groups_complex_cycle",
            [
                "Cyclic dependency group include in test: coverage -> dev -> test",
                "Cyclic dependency group include in coverage: dev -> test -> coverage",
                "Cyclic dependency group include in dev: test -> coverage -> dev",
            ],
        ),
    ],
)
def test_create_poetry_with_dependency_groups_simple_cycle(
    fixture: str, expected: list[str]
) -> None:
    with pytest.raises(RuntimeError) as e:
        _ = Factory().create_poetry(fixtures_dir / fixture)

    assert all(exp in str(e.value) for exp in expected)


def test_create_poetry_with_groups_and_legacy_dev(caplog: LogCaptureFixture) -> None:
    assert not caplog.records

    poetry = Factory().create_poetry(
        fixtures_dir / "project_with_groups_and_legacy_dev"
    )

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "WARNING"
    assert '"poetry.dev-dependencies" section is deprecated' in record.message

    package = poetry.package
    dependencies = package.all_requires

    assert len(dependencies) == 2
    assert {dependency.name for dependency in dependencies} == {"pytest", "pre-commit"}


def test_create_poetry_with_groups_and_explicit_main() -> None:
    poetry = Factory().create_poetry(
        fixtures_dir / "project_with_groups_and_explicit_main"
    )

    package = poetry.package
    dependencies = package.requires

    assert len(dependencies) == 1
    assert {dependency.name for dependency in dependencies} == {
        "aiohttp",
    }


def test_create_poetry_with_markers_and_extras() -> None:
    poetry = Factory().create_poetry(fixtures_dir / "project_with_markers_and_extras")

    package = poetry.package
    dependencies = package.requires
    extras = package.extras

    assert len(dependencies) == 2
    assert {dependency.name for dependency in dependencies} == {"orjson"}
    assert set(extras[canonicalize_name("all")]) == set(dependencies)
    for dependency in dependencies:
        assert dependency.in_extras == ["all"]
        assert isinstance(dependency, URLDependency)
        assert isinstance(dependency.marker, SingleMarker)
        assert dependency.marker.name == "sys_platform"
        assert dependency.marker.value == (
            "darwin" if "macosx" in dependency.url else "linux"
        )


@pytest.mark.parametrize(
    "constraint, exp_python, exp_marker",
    [
        ({"python": "3.7"}, "~3.7", 'python_version == "3.7"'),
        ({"platform": "linux"}, "*", 'sys_platform == "linux"'),
        ({"markers": 'python_version == "3.7"'}, "~3.7", 'python_version == "3.7"'),
        (
            {"markers": 'platform_machine == "x86_64"'},
            "*",
            'platform_machine == "x86_64"',
        ),
        (
            {"python": "3.7", "markers": 'platform_machine == "x86_64"'},
            "~3.7",
            'platform_machine == "x86_64" and python_version == "3.7"',
        ),
        (
            {"platform": "linux", "markers": 'platform_machine == "x86_64"'},
            "*",
            'platform_machine == "x86_64" and sys_platform == "linux"',
        ),
        (
            {
                "python": "3.7",
                "platform": "linux",
                "markers": 'platform_machine == "x86_64"',
            },
            "~3.7",
            (
                'platform_machine == "x86_64" and python_version == "3.7" and'
                ' sys_platform == "linux"'
            ),
        ),
        (
            {"python": ">=3.7", "markers": 'python_version < "4.0"'},
            "<4.0 >=3.7",
            'python_version < "4.0" and python_version >= "3.7"',
        ),
        (
            {"platform": "linux", "markers": 'sys_platform == "win32"'},
            "*",
            "<empty>",
        ),
    ],
)
def test_create_dependency_marker_variants(
    constraint: dict[str, Any], exp_python: str, exp_marker: str
) -> None:
    constraint["version"] = "1.0.0"
    dep = Factory.create_dependency("foo", constraint)
    assert dep.python_versions == exp_python
    assert dep.python_constraint == parse_constraint(exp_python)
    assert str(dep.marker) == exp_marker


@pytest.mark.parametrize(
    ("constraint", "expected"),
    [
        ("1", None),
        ({"version": "1"}, None),
        ({"version": "1", "allow-prereleases": False}, False),
        ({"version": "1", "allow-prereleases": True}, True),
    ],
)
def test_create_dependency_allow_prereleases(
    constraint: str | dict[str, str], expected: bool | None
) -> None:
    dep = Factory.create_dependency("foo", constraint)
    assert dep.allows_prereleases() is expected


def test_all_classifiers_unique_even_if_classifiers_is_duplicated() -> None:
    poetry = Factory().create_poetry(
        fixtures_dir / "project_with_duplicated_classifiers"
    )
    package = poetry.package
    assert package.all_classifiers == [
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Software Development :: Build Tools",
    ]


@pytest.mark.parametrize(
    ("project", "expected"),
    [
        ("sample_project", set(BuildSystem().dependencies)),
        (
            "project_with_build_system_requires",
            {
                Dependency.create_from_pep_508("poetry-core"),
                Dependency.create_from_pep_508("Cython (>=0.29.6,<0.30.0)"),
            },
        ),
    ],
)
def test_poetry_build_system_dependencies_from_fixtures(
    project: str, expected: set[Dependency]
) -> None:
    poetry = Factory().create_poetry(fixtures_dir / project)
    assert set(poetry.build_system_dependencies) == expected


SAMPLE_PROJECT_DIRECTORY = fixtures_dir / "sample_project"
SIMPLE_PROJECT_WHEEL = (
    fixtures_dir
    / "simple_project"
    / "dist"
    / "simple_project-1.2.3-py2.py3-none-any.whl"
)


@pytest.mark.parametrize(
    ("requires", "expected"),
    [
        (BuildSystem().requires, set(BuildSystem().dependencies)),
        (["poetry-core>=2.0.0"], {Dependency("poetry-core", ">=2.0.0")}),
        (["****invalid****"], set()),
        (
            ["hatch", "numpy ; sys_platform == 'win32'"],
            {
                Dependency("hatch", "*"),
                Dependency.create_from_pep_508("numpy ; sys_platform == 'win32'"),
            },
        ),
        (
            [SAMPLE_PROJECT_DIRECTORY.as_posix()],
            {
                DirectoryDependency(
                    SAMPLE_PROJECT_DIRECTORY.name, SAMPLE_PROJECT_DIRECTORY
                )
            },
        ),
        (
            [SIMPLE_PROJECT_WHEEL.as_posix()],
            {FileDependency(SIMPLE_PROJECT_WHEEL.name, SIMPLE_PROJECT_WHEEL)},
        ),
    ],
)
def test_poetry_build_system_dependencies(
    requires: list[str], expected: set[Dependency], temporary_directory: Path
) -> None:
    pyproject_toml = temporary_directory / "pyproject.toml"
    build_system_requires = ", ".join(f'"{require}"' for require in requires)
    content = f"""[project]
name = "my-package"
version = "1.2.3"

[build-system]
requires = [{build_system_requires}]
build-backend = "some.api.we.do.not.care.about"

"""
    pyproject_toml.write_text(content, encoding="utf-8")
    poetry = Factory().create_poetry(temporary_directory)

    assert set(poetry.build_system_dependencies) == expected


@pytest.mark.parametrize("in_order", [True, False])
@pytest.mark.parametrize(
    ("group_name", "included_group_name"),
    [
        ("testing", "testing"),
        ("testing", "TESTING"),
        ("group_a", "group-a"),
        # Examples from the PEP 508 spec
        # https://packaging.python.org/en/latest/specifications/name-normalization/#valid-non-normalized-names
        ("friendly-bard", "friendly-bard"),
        ("friendly-bard", "Friendly-Bard"),
        ("friendly-bard", "FRIENDLY-BARD"),
        ("friendly-bard", "friendly.bard"),
        ("friendly-bard", "friendly_bard"),
        ("friendly-bard", "friendly--bard"),
        ("friendly-bard", "FrIeNdLy-._.-bArD"),
        ("friendly-Bard", "friendly-bard"),
        ("FRIENDLY-BARD", "friendly-bard"),
        ("friendly.bard", "friendly-bard"),
        ("friendly_bard", "friendly-bard"),
        ("friendly--bard", "friendly-bard"),
        ("FrIeNdLy-._.-bArD", "friendly-bard"),
    ],
)
def test_create_poetry_with_nested_dependency_groups(
    group_name: str, included_group_name: str, in_order: bool, temporary_directory: Path
) -> None:
    pyproject_toml = temporary_directory / "pyproject.toml"

    replace_group_name = "%REPLACE_GROUP_NAME%"
    replace_included_group_name = "%REPLACE_INCLUDED_GROUP_NAME%"
    in_order_content = """\
[project]
name = "my-package"
version = "1.2.3"

[tool.poetry.group.%REPLACE_GROUP_NAME%.dependencies]
pytest = "*"
pytest-cov ="*"

[tool.poetry.group.dev]
include-groups = [
    "%REPLACE_INCLUDED_GROUP_NAME%",
]
[tool.poetry.group.dev.dependencies]
black = "*"
"""
    # The dev group refers to a group that is defined after it.
    out_of_order_content = """\
[project]
name = "my-package"
version = "1.2.3"

[tool.poetry.group.dev]
include-groups = [
    "%REPLACE_INCLUDED_GROUP_NAME%",
]
[tool.poetry.group.dev.dependencies]
black = "*"

[tool.poetry.group.%REPLACE_GROUP_NAME%.dependencies]
pytest = "*"
pytest-cov ="*"
"""

    # Generate the content. If `group_name` has a `.` in it, we "escape" it with
    # quotes to make it a valid TOML key.
    base_content = in_order_content if in_order else out_of_order_content
    group_name_to_use = group_name if "." not in group_name else f'"{group_name}"'
    content = base_content.replace(replace_group_name, group_name_to_use).replace(
        replace_included_group_name, included_group_name
    )

    pyproject_toml.write_text(content, encoding="utf-8")
    poetry = Factory().create_poetry(temporary_directory)

    # Groups are reported internally using their canonical names.
    canonical_name = canonicalize_name(group_name)

    assert len(poetry.package.all_requires) == 5
    assert sorted(
        [(dep.name, ",".join(dep.groups)) for dep in poetry.package.all_requires],
        key=lambda x: x[0] + x[1],
    ) == sorted(
        [
            ("black", "dev"),
            ("pytest-cov", "dev"),
            ("pytest-cov", canonical_name),
            ("pytest", "dev"),
            ("pytest", canonical_name),
        ],
        key=lambda x: x[0] + x[1],
    )


def assert_invalid_group_including(
    toml_data: str,
    expected_error: str,
    error_type: type[Exception],
    temporary_directory: Path,
) -> None:
    pyproject_toml = temporary_directory / "pyproject.toml"
    pyproject_toml.write_text(toml_data, encoding="utf-8")

    with pytest.raises(error_type) as error:
        _ = Factory().create_poetry(temporary_directory)

    assert str(error.value) == expected_error


@pytest.mark.parametrize(
    "include_group_name", ["testing_group", "Testing-Group", "testing-group"]
)
def test_create_poetry_with_self_referenced_dependency_groups(
    include_group_name: str,
    temporary_directory: Path,
) -> None:
    """testing-group -> testing-group"""
    content = f"""\
[project]
name = "my-package"
version = "1.2.3"

[tool.poetry.group.testing-group]
include-groups = [
    "{include_group_name}",
]

[tool.poetry.group.testing-group.dependencies]
pytest = "*"
pytest-cov ="*"
"""

    expected = """\
The Poetry configuration is invalid:
  - Cyclic dependency group include in testing-group: testing-group
"""
    assert_invalid_group_including(
        toml_data=content,
        expected_error=expected,
        error_type=RuntimeError,
        temporary_directory=temporary_directory,
    )


def test_create_poetry_with_direct_cyclic_dependency_groups(
    temporary_directory: Path,
) -> None:
    """
    testing -> dev
    dev -> testing
    """
    content = """\
[project]
name = "my-package"
version = "1.2.3"

[tool.poetry.group.testing]
include-groups = [
    "dev",
]

[tool.poetry.group.testing.dependencies]
pytest = "*"
pytest-cov ="*"

[tool.poetry.group.dev]
include-groups = [
    "testing",
]
[tool.poetry.group.dev.dependencies]
black = "*"
"""

    expected = """\
The Poetry configuration is invalid:
  - Cyclic dependency group include in testing: dev -> testing
  - Cyclic dependency group include in dev: testing -> dev
"""
    assert_invalid_group_including(
        toml_data=content,
        expected_error=expected,
        error_type=RuntimeError,
        temporary_directory=temporary_directory,
    )


def test_create_poetry_with_indirect_full_cyclic_dependency_groups(
    temporary_directory: Path,
) -> None:
    """
    group-1 -> group-3
    group-2 -> group-1
    group-3 -> group-2
    """
    content = """\
[project]
name = "my-package"
version = "1.2.3"

[tool.poetry.group.group_1]
include-groups = [
    "group_3",
]

[tool.poetry.group.group_1.dependencies]
foo = "*"

[tool.poetry.group.group_2]
include-groups = [
    "group_1",
]
[tool.poetry.group.group_2.dependencies]
bar = "*"

[tool.poetry.group.group_3]
include-groups = [
    "group_2",
]
[tool.poetry.group.group_3.dependencies]
baz = "*"
"""

    expected = """\
The Poetry configuration is invalid:
  - Cyclic dependency group include in group-1: group-3 -> group-2 -> group-1
  - Cyclic dependency group include in group-2: group-1 -> group-3 -> group-2
  - Cyclic dependency group include in group-3: group-2 -> group-1 -> group-3
"""
    assert_invalid_group_including(
        toml_data=content,
        expected_error=expected,
        error_type=RuntimeError,
        temporary_directory=temporary_directory,
    )


def test_create_poetry_with_indirect_partial_cyclic_dependency_groups(
    temporary_directory: Path,
) -> None:
    """
    group-1 -> group-2
    group-2 -> group-1
    group-3 -> group-2
    """
    content = """\
[project]
name = "my-package"
version = "1.2.3"

[tool.poetry.group.group_1]
include-groups = [
    "group_2",
]

[tool.poetry.group.group_1.dependencies]
foo = "*"

[tool.poetry.group.group_2]
include-groups = [
    "group_1",
]
[tool.poetry.group.group_2.dependencies]
bar = "*"

[tool.poetry.group.group_3]
include-groups = [
    "group_2",
]
[tool.poetry.group.group_3.dependencies]
baz = "*"
"""

    expected = """\
The Poetry configuration is invalid:
  - Cyclic dependency group include in group-1: group-2 -> group-1
  - Cyclic dependency group include in group-2: group-1 -> group-2
  - Cyclic dependency group include in group-3: group-2 -> group-1 -> group-2
"""
    assert_invalid_group_including(
        toml_data=content,
        expected_error=expected,
        error_type=RuntimeError,
        temporary_directory=temporary_directory,
    )


def test_create_poetry_with_shared_dependency_groups(
    temporary_directory: Path,
) -> None:
    """
    root -> child-1, child-2
    child-1 -> shared
    child-2 -> shared
    """
    content = """\
[project]
name = "my-package"
version = "1.2.3"

[tool.poetry.group.root]
include-groups = [
    "child_1",
    "child_2",
]

[tool.poetry.group.root.dependencies]
foo = "*"

[tool.poetry.group.child_1]
include-groups = [
    "shared",
]
[tool.poetry.group.child_1.dependencies]
bar = "*"

[tool.poetry.group.child_2]
include-groups = [
    "shared",
]
[tool.poetry.group.child_2.dependencies]
baz = "*"

[tool.poetry.group.shared.dependencies]
quux = "*"
"""
    pyproject_toml = temporary_directory / "pyproject.toml"
    pyproject_toml.write_text(content, encoding="utf-8")
    poetry = Factory().create_poetry(temporary_directory)

    assert len(poetry.package.all_requires) == 10
    assert sorted(
        [(dep.name, ",".join(dep.groups)) for dep in poetry.package.all_requires],
        key=lambda x: x[0] + x[1],
    ) == [
        ("bar", "child-1"),
        ("bar", "root"),
        ("baz", "child-2"),
        ("baz", "root"),
        ("foo", "root"),
        ("quux", "child-1"),
        ("quux", "child-2"),
        # Duplicates because dependency is included via several groups.
        # This is ok because they are merged during dependency resolution.
        ("quux", "root"),
        ("quux", "root"),
        ("quux", "shared"),
    ]


def test_create_poetry_with_shared_dependency_groups_more_complicated(
    temporary_directory: Path,
) -> None:
    """
    root -> child-1, child-2
    child-1 -> shared
    child-2 -> grandchild
    grandchild -> shared
    """
    content = """\
[project]
name = "my-package"
version = "1.2.3"

[tool.poetry.group.root]
include-groups = [
    "child_1",
    "child_2",
]

[tool.poetry.group.root.dependencies]
foo = "*"

[tool.poetry.group.child_1]
include-groups = [
    "shared",
]
[tool.poetry.group.child_1.dependencies]
bar = "*"

[tool.poetry.group.child_2]
include-groups = [
    "grandchild",
]
[tool.poetry.group.child_2.dependencies]
baz = "*"

[tool.poetry.group.grandchild]
include-groups = [
    "shared",
]
[tool.poetry.group.grandchild.dependencies]
bax = "*"

[tool.poetry.group.shared.dependencies]
quux = "*"
"""
    pyproject_toml = temporary_directory / "pyproject.toml"
    pyproject_toml.write_text(content, encoding="utf-8")
    poetry = Factory().create_poetry(temporary_directory)

    assert len(poetry.package.all_requires) == 14
    assert sorted(
        [(dep.name, ",".join(dep.groups)) for dep in poetry.package.all_requires],
        key=lambda x: x[0] + x[1],
    ) == [
        ("bar", "child-1"),
        ("bar", "root"),
        ("bax", "child-2"),
        ("bax", "grandchild"),
        ("bax", "root"),
        ("baz", "child-2"),
        ("baz", "root"),
        ("foo", "root"),
        ("quux", "child-1"),
        ("quux", "child-2"),
        ("quux", "grandchild"),
        # Duplicates because dependency is included via several groups.
        # This is ok because they are merged during dependency resolution.
        ("quux", "root"),
        ("quux", "root"),
        ("quux", "shared"),
    ]


def test_create_poetry_with_complicated_cyclic_diamond_dependency_groups(
    temporary_directory: Path,
) -> None:
    """
    root -> child-1, child-2
    child-1 -> shared
    child-2 -> shared
    shared -> grandchild
    grandchild -> child-2
    """
    content = """\
[project]
name = "my-package"
version = "1.2.3"

[tool.poetry.group.root]
include-groups = [
    "child_1",
    "child_2",
]

[tool.poetry.group.root.dependencies]
foo = "*"

[tool.poetry.group.child_1]
include-groups = [
    "shared",
]
[tool.poetry.group.child_1.dependencies]
bar = "*"

[tool.poetry.group.child_2]
include-groups = [
    "shared",
]
[tool.poetry.group.child_2.dependencies]
baz = "*"

[tool.poetry.group.shared]
include-groups = [
    "grandchild",
]
[tool.poetry.group.shared.dependencies]
quux = "*"

[tool.poetry.group.grandchild]
include-groups = [
    "child_2",
]
[tool.poetry.group.grandchild.dependencies]
bar = "*"
"""

    expected = """\
The Poetry configuration is invalid:
  - Cyclic dependency group include in root: child-2 -> shared -> grandchild -> child-2
  - Cyclic dependency group include in root: child-1 -> shared -> grandchild -> child-2 -> shared
  - Cyclic dependency group include in child-1: shared -> grandchild -> child-2 -> shared
  - Cyclic dependency group include in child-2: shared -> grandchild -> child-2
  - Cyclic dependency group include in shared: grandchild -> child-2 -> shared
  - Cyclic dependency group include in grandchild: child-2 -> shared -> grandchild
"""

    assert_invalid_group_including(
        toml_data=content,
        expected_error=expected,
        error_type=RuntimeError,
        temporary_directory=temporary_directory,
    )


def test_create_poetry_with_noncanonical_names_cyclic_dependency_groups(
    temporary_directory: Path,
) -> None:
    """
    group-1 -> group-2
    group-2 -> group-1
    group-3 -> group-2
    """
    content = """\
[project]
name = "my-package"
version = "1.2.3"

[tool.poetry.group.GROUP_1]
include-groups = [
    "gRoup_2",
]

[tool.poetry.group.GROUP_1.dependencies]
foo = "*"

[tool.poetry.group.group_2]
include-groups = [
    "groUp_1",
]
[tool.poetry.group.group_2.dependencies]
bar = "*"

[tool.poetry.group.group_3]
include-groups = [
    "group_2",
]
[tool.poetry.group.group_3.dependencies]
baz = "*"
"""

    expected = """\
The Poetry configuration is invalid:
  - Cyclic dependency group include in group-1: group-2 -> group-1
  - Cyclic dependency group include in group-2: group-1 -> group-2
  - Cyclic dependency group include in group-3: group-2 -> group-1 -> group-2
"""
    assert_invalid_group_including(
        toml_data=content,
        expected_error=expected,
        error_type=RuntimeError,
        temporary_directory=temporary_directory,
    )


def test_create_poetry_with_unknown_nested_dependency_groups(
    temporary_directory: Path,
) -> None:
    content = """\
[project]
name = "my-package"
version = "1.2.3"

[tool.poetry.group.dev]
include-groups = [
    "testing",
]
[tool.poetry.group.dev.dependencies]
black = "*"
"""
    expected = "Group 'dev' includes group 'testing' which is not defined."

    assert_invalid_group_including(
        toml_data=content,
        expected_error=expected,
        error_type=ValueError,
        temporary_directory=temporary_directory,
    )


def test_create_poetry_with_included_groups_only(temporary_directory: Path) -> None:
    pyproject_toml = temporary_directory / "pyproject.toml"
    content = """\
[project]
name = "my-package"
version = "1.2.3"

[tool.poetry.group.lint.dependencies]
black = "*"

[tool.poetry.group.testing.dependencies]
pytest = "*"

[tool.poetry.group.all]
include-groups = [
    "lint",
    "testing",
]
"""
    pyproject_toml.write_text(content, encoding="utf-8")

    poetry = Factory().create_poetry(temporary_directory)
    assert len(poetry.package.all_requires) == 4
    assert [
        (dep.name, ",".join(dep.groups)) for dep in poetry.package.all_requires
    ] == [
        ("black", "lint"),
        ("pytest", "testing"),
        ("black", "all"),
        ("pytest", "all"),
    ]


def test_create_poetry_with_nested_similar_dependencies(
    temporary_directory: Path,
) -> None:
    pyproject_toml = temporary_directory / "pyproject.toml"
    content = """\
[project]
name = "my-package"
version = "1.2.3"

[tool.poetry.group.parent.dependencies]
foo = "*"

[tool.poetry.group.parent]
include-groups = [
    "child",
]

[tool.poetry.group.child.dependencies]
foo = "*"

"""

    pyproject_toml.write_text(content, encoding="utf-8")

    poetry = Factory().create_poetry(temporary_directory)
    assert len(poetry.package.all_requires) == 3
    assert [
        (dep.name, ",".join(dep.groups)) for dep in poetry.package.all_requires
    ] == [
        # Duplicates because dependency is included via several groups.
        # This is ok because they are merged during dependency resolution.
        ("foo", "parent"),
        ("foo", "parent"),
        ("foo", "child"),
    ]
