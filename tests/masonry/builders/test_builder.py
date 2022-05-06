from __future__ import annotations

import sys

from email.parser import Parser
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from poetry.core.factory import Factory
from poetry.core.masonry.builders.builder import Builder


if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_builder_find_excluded_files(mocker: MockerFixture) -> None:
    p = mocker.patch("poetry.core.vcs.git.Git.get_ignored_files")
    p.return_value = []

    builder = Builder(
        Factory().create_poetry(Path(__file__).parent / "fixtures" / "complete")
    )

    assert builder.find_excluded_files() == {"my_package/sub_pkg1/extra_file.xml"}


@pytest.mark.xfail(
    sys.platform == "win32",
    reason="Windows is case insensitive for the most part",
)
def test_builder_find_case_sensitive_excluded_files(mocker: MockerFixture) -> None:
    p = mocker.patch("poetry.core.vcs.git.Git.get_ignored_files")
    p.return_value = []

    builder = Builder(
        Factory().create_poetry(
            Path(__file__).parent / "fixtures" / "case_sensitive_exclusions"
        )
    )

    assert builder.find_excluded_files() == {
        "my_package/FooBar/Bar.py",
        "my_package/FooBar/lowercasebar.py",
        "my_package/Foo/SecondBar.py",
        "my_package/Foo/Bar.py",
        "my_package/Foo/lowercasebar.py",
        "my_package/bar/foo.py",
        "my_package/bar/CapitalFoo.py",
    }


@pytest.mark.xfail(
    sys.platform == "win32",
    reason="Windows is case insensitive for the most part",
)
def test_builder_find_invalid_case_sensitive_excluded_files(
    mocker: MockerFixture,
) -> None:
    p = mocker.patch("poetry.core.vcs.git.Git.get_ignored_files")
    p.return_value = []

    builder = Builder(
        Factory().create_poetry(
            Path(__file__).parent / "fixtures" / "invalid_case_sensitive_exclusions"
        )
    )

    assert {"my_package/Bar/foo/bar/Foo.py"} == builder.find_excluded_files()


def test_get_metadata_content() -> None:
    builder = Builder(
        Factory().create_poetry(Path(__file__).parent / "fixtures" / "complete")
    )

    metadata = builder.get_metadata_content()

    p = Parser()
    parsed = p.parsestr(metadata)

    assert parsed["Metadata-Version"] == "2.1"
    assert parsed["Name"] == "my-package"
    assert parsed["Version"] == "1.2.3"
    assert parsed["Summary"] == "Some description."
    assert parsed["Author"] == "Sébastien Eustace"
    assert parsed["Author-email"] == "sebastien@eustace.io"
    assert parsed["Keywords"] == "packaging,dependency,poetry"
    assert parsed["Requires-Python"] == ">=3.6,<4.0"
    assert parsed["License"] == "MIT"
    assert parsed["Home-page"] == "https://python-poetry.org/"

    classifiers = parsed.get_all("Classifier")
    assert classifiers == [
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]

    extras = parsed.get_all("Provides-Extra")
    assert extras == ["time"]

    requires = parsed.get_all("Requires-Dist")
    assert requires == [
        "cachy[msgpack] (>=0.2.0,<0.3.0)",
        "cleo (>=0.6,<0.7)",
        'pendulum (>=1.4,<2.0); (python_version ~= "2.7" and sys_platform == "win32" or'
        ' python_version in "3.4 3.5") and (extra == "time")',
    ]

    urls = parsed.get_all("Project-URL")
    assert urls == [
        "Documentation, https://python-poetry.org/docs",
        "Issue Tracker, https://github.com/python-poetry/poetry/issues",
        "Repository, https://github.com/python-poetry/poetry",
    ]


def test_metadata_homepage_default() -> None:
    builder = Builder(
        Factory().create_poetry(Path(__file__).parent / "fixtures" / "simple_version")
    )

    metadata = Parser().parsestr(builder.get_metadata_content())

    assert metadata["Home-page"] is None


def test_metadata_with_vcs_dependencies() -> None:
    builder = Builder(
        Factory().create_poetry(
            Path(__file__).parent / "fixtures" / "with_vcs_dependency"
        )
    )

    metadata = Parser().parsestr(builder.get_metadata_content())

    requires_dist = metadata["Requires-Dist"]

    assert requires_dist == "cleo @ git+https://github.com/sdispater/cleo.git@master"


def test_metadata_with_url_dependencies() -> None:
    builder = Builder(
        Factory().create_poetry(
            Path(__file__).parent / "fixtures" / "with_url_dependency"
        )
    )

    metadata = Parser().parsestr(builder.get_metadata_content())

    requires_dist = metadata["Requires-Dist"]

    assert (
        requires_dist
        == "demo @"
        " https://python-poetry.org/distributions/demo-0.1.0-py2.py3-none-any.whl"
    )


def test_missing_script_files_throws_error() -> None:
    builder = Builder(
        Factory().create_poetry(
            Path(__file__).parent / "fixtures" / "script_reference_file_missing"
        )
    )

    with pytest.raises(RuntimeError) as err:
        builder.convert_script_files()

    assert "is not found." in err.value.args[0]


def test_invalid_script_files_definition() -> None:
    with pytest.raises(RuntimeError) as err:
        Builder(
            Factory().create_poetry(
                Path(__file__).parent
                / "fixtures"
                / "script_reference_file_invalid_definition"
            )
        )

    assert "configuration is invalid" in err.value.args[0]
    assert "[scripts.invalid_definition]" in err.value.args[0]


@pytest.mark.parametrize(
    "fixture",
    [
        "script_callable_legacy_table",
    ],
)
def test_entrypoint_scripts_legacy_warns(fixture: str) -> None:
    with pytest.warns(DeprecationWarning):
        Builder(
            Factory().create_poetry(Path(__file__).parent / "fixtures" / fixture)
        ).convert_entry_points()


@pytest.mark.parametrize(
    "fixture, result",
    [
        (
            "script_callable_legacy_table",
            {
                "console_scripts": [
                    "extra-script-legacy = my_package.extra_legacy:main",
                    "script-legacy = my_package.extra_legacy:main",
                ]
            },
        ),
        (
            "script_callable_legacy_string",
            {"console_scripts": ["script-legacy = my_package:main"]},
        ),
        (
            "script_reference_console",
            {
                "console_scripts": [
                    "extra-script = my_package.extra:main[time]",
                    "script = my_package.extra:main",
                ]
            },
        ),
        (
            "script_reference_file",
            {},
        ),
    ],
)
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_builder_convert_entry_points(
    fixture: str, result: dict[str, list[str]]
) -> None:
    entry_points = Builder(
        Factory().create_poetry(Path(__file__).parent / "fixtures" / fixture)
    ).convert_entry_points()
    assert entry_points == result


@pytest.mark.parametrize(
    "fixture, result",
    [
        (
            "script_callable_legacy_table",
            [],
        ),
        (
            "script_callable_legacy_string",
            [],
        ),
        (
            "script_reference_console",
            [],
        ),
        (
            "script_reference_file",
            [Path("bin") / "script.sh"],
        ),
    ],
)
def test_builder_convert_script_files(fixture: str, result: list[Path]) -> None:
    project_root = Path(__file__).parent / "fixtures" / fixture
    script_files = Builder(Factory().create_poetry(project_root)).convert_script_files()
    assert [p.relative_to(project_root) for p in script_files] == result


def test_metadata_with_readme_files() -> None:
    test_path = Path(__file__).parent.parent.parent / "fixtures" / "with_readme_files"
    builder = Builder(Factory().create_poetry(test_path))

    metadata = Parser().parsestr(builder.get_metadata_content())

    readme1 = test_path / "README-1.rst"
    readme2 = test_path / "README-2.rst"
    description = "\n".join([readme1.read_text(), readme2.read_text(), ""])

    assert metadata.get_payload() == description


def test_metadata_with_wildcard_dependency_constraint() -> None:
    test_path = (
        Path(__file__).parent / "fixtures" / "with_wildcard_dependency_constraint"
    )
    builder = Builder(Factory().create_poetry(test_path))

    metadata = Parser().parsestr(builder.get_metadata_content())

    requires = metadata.get_all("Requires-Dist")
    assert requires == ["google-api-python-client (>=1.8,!=2.0.*)"]
