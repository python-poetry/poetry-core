from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import cast

import pytest

from poetry.core.factory import Factory
from poetry.core.packages.vcs_dependency import VCSDependency
from poetry.core.semver.helpers import parse_constraint
from poetry.core.toml import TOMLFile


fixtures_dir = Path(__file__).parent / "fixtures"


def test_create_poetry() -> None:
    poetry = Factory().create_poetry(fixtures_dir / "sample_project")

    package = poetry.package

    assert package.name == "my-package"
    assert package.version.text == "1.2.3"
    assert package.description == "Some description."
    assert package.authors == ["Sébastien Eustace <sebastien@eustace.io>"]
    assert package.license
    assert package.license.id == "MIT"
    assert (
        package.readmes[0].relative_to(fixtures_dir).as_posix()
        == "sample_project/README.rst"
    )
    assert package.homepage == "https://python-poetry.org"
    assert package.repository_url == "https://github.com/python-poetry/poetry"
    assert package.keywords == ["packaging", "dependency", "poetry"]

    assert package.python_versions == "~2.7 || ^3.6"
    assert str(package.python_constraint) == ">=2.7,<2.8 || >=3.6,<4.0"

    dependencies = {}
    for dep in package.requires:
        dependencies[dep.name] = dep

    cleo = dependencies["cleo"]
    assert cleo.pretty_constraint == "^0.6"
    assert not cleo.is_optional()

    pendulum = dependencies["pendulum"]
    assert pendulum.pretty_constraint == "branch 2.0"
    assert pendulum.is_vcs()
    pendulum = cast(VCSDependency, pendulum)
    assert pendulum.vcs == "git"
    assert pendulum.branch == "2.0"
    assert pendulum.source == "https://github.com/sdispater/pendulum.git"
    assert pendulum.allows_prereleases()
    assert not pendulum.develop

    tomlkit = dependencies["tomlkit"]
    assert tomlkit.pretty_constraint == "rev 3bff550"
    assert tomlkit.is_vcs()
    tomlkit = cast(VCSDependency, tomlkit)
    assert tomlkit.vcs == "git"
    assert tomlkit.rev == "3bff550"
    assert tomlkit.source == "https://github.com/sdispater/tomlkit.git"
    assert tomlkit.allows_prereleases()
    assert not tomlkit.develop

    requests = dependencies["requests"]
    assert requests.pretty_constraint == "^2.18"
    assert not requests.is_vcs()
    assert not requests.allows_prereleases()
    assert requests.is_optional()
    assert requests.extras == frozenset({"security"})

    pathlib2 = dependencies["pathlib2"]
    assert pathlib2.pretty_constraint == "^2.2"
    assert pathlib2.python_versions == ">=2.7 <2.8"
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
    assert functools32.pretty_constraint == "^3.2.3"
    assert (
        str(functools32.marker)
        == 'python_version ~= "2.7" and sys_platform == "win32" or python_version in'
        ' "3.4 3.5"'
    )

    dataclasses = dependencies["dataclasses"]
    assert dataclasses.name == "dataclasses"
    assert dataclasses.pretty_constraint == "^0.7"
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

    assert package.all_classifiers == [
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]


def test_create_poetry_with_packages_and_includes() -> None:
    poetry = Factory().create_poetry(
        fixtures_dir.parent / "masonry" / "builders" / "fixtures" / "with-include"
    )

    package = poetry.package

    assert package.packages == [
        {"include": "extra_dir/**/*.py"},
        {"include": "extra_dir/**/*.py"},
        {"include": "my_module.py"},
        {"include": "package_with_include"},
        {"include": "tests", "format": "sdist"},
        {"include": "for_wheel_only", "format": ["wheel"]},
        {"include": "src_package", "from": "src"},
    ]

    assert package.include == [
        {"path": "extra_dir/vcs_excluded.txt", "format": []},
        {"path": "notes.txt", "format": []},
    ]


def test_create_poetry_with_multi_constraints_dependency() -> None:
    poetry = Factory().create_poetry(
        fixtures_dir / "project_with_multi_constraints_dependency"
    )

    package = poetry.package

    assert len(package.requires) == 2


def test_validate() -> None:
    complete = TOMLFile(fixtures_dir / "complete.toml")
    doc: dict[str, Any] = complete.read()
    content = doc["tool"]["poetry"]

    assert Factory.validate(content) == {"errors": [], "warnings": []}


def test_validate_fails() -> None:
    complete = TOMLFile(fixtures_dir / "complete.toml")
    doc: dict[str, Any] = complete.read()
    content = doc["tool"]["poetry"]
    content["this key is not in the schema"] = ""

    expected = (
        "Additional properties are not allowed "
        "('this key is not in the schema' was unexpected)"
    )

    assert Factory.validate(content) == {"errors": [expected], "warnings": []}


def test_strict_validation_success_on_multiple_readme_files() -> None:
    with_readme_files = TOMLFile(fixtures_dir / "with_readme_files" / "pyproject.toml")
    doc: dict[str, Any] = with_readme_files.read()
    content = doc["tool"]["poetry"]

    assert Factory.validate(content, strict=True) == {"errors": [], "warnings": []}


def test_strict_validation_fails_on_readme_files_with_unmatching_types() -> None:
    with_readme_files = TOMLFile(fixtures_dir / "with_readme_files" / "pyproject.toml")
    doc: dict[str, Any] = with_readme_files.read()
    content = doc["tool"]["poetry"]
    content["readme"][0] = "README.md"

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
  - 'description' is a required property
"""
    assert str(e.value) == expected


def test_create_poetry_omits_dev_dependencies_iff_with_dev_is_false() -> None:
    poetry = Factory().create_poetry(fixtures_dir / "sample_project", with_groups=False)
    assert not any("dev" in r.groups for r in poetry.package.all_requires)

    poetry = Factory().create_poetry(fixtures_dir / "sample_project")
    assert any("dev" in r.groups for r in poetry.package.all_requires)


def test_create_poetry_fails_with_invalid_dev_dependencies_iff_with_dev_is_true() -> None:
    with pytest.raises(ValueError) as err:
        Factory().create_poetry(fixtures_dir / "project_with_invalid_dev_deps")
    assert "does not exist" in str(err.value)

    Factory().create_poetry(
        fixtures_dir / "project_with_invalid_dev_deps", with_groups=False
    )


def test_create_poetry_with_groups_and_legacy_dev() -> None:
    poetry = Factory().create_poetry(
        fixtures_dir / "project_with_groups_and_legacy_dev"
    )

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
            'platform_machine == "x86_64" and python_version == "3.7" and sys_platform'
            ' == "linux"',
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
