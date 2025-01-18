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


def test_building_not_possible_in_non_package_mode() -> None:
    with pytest.raises(RuntimeError) as err:
        Builder(
            Factory().create_poetry(
                Path(__file__).parent.parent.parent / "fixtures" / "non_package_mode"
            )
        )

    assert str(err.value) == "Building a package is not possible in non-package mode."


def test_builder_find_excluded_files(mocker: MockerFixture) -> None:
    mocker.patch("poetry.core.vcs.git.Git.get_ignored_files", return_value=[])

    builder = Builder(
        Factory().create_poetry(Path(__file__).parent / "fixtures" / "complete")
    )

    assert builder.find_excluded_files() == {"my_package/sub_pkg1/extra_file.xml"}


@pytest.mark.xfail(
    sys.platform == "win32",
    reason="Windows is case insensitive for the most part",
)
def test_builder_find_case_sensitive_excluded_files(mocker: MockerFixture) -> None:
    mocker.patch("poetry.core.vcs.git.Git.get_ignored_files", return_value=[])

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
    mocker.patch("poetry.core.vcs.git.Git.get_ignored_files", return_value=[])

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

    assert parsed["Metadata-Version"] == "2.3"
    assert parsed["Name"] == "my-package"
    assert parsed["Version"] == "1.2.3"
    assert parsed["Summary"] == "Some description."
    assert parsed["Author"] == "Sébastien Eustace"
    assert parsed["Author-email"] == "sebastien@eustace.io"
    assert parsed["Keywords"] == "packaging,dependency,poetry"
    assert parsed["Requires-Python"] == ">=3.6,<4.0"
    assert parsed["License"] == "MIT"
    assert parsed["Home-page"] is None

    classifiers = parsed.get_all("Classifier")
    assert classifiers == [
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
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]

    extras = parsed.get_all("Provides-Extra")
    assert extras == ["time"]

    requires = parsed.get_all("Requires-Dist")
    assert requires == [
        "cachy[msgpack] (>=0.2.0,<0.3.0)",
        "cleo (>=0.6,<0.7)",
        (
            'pendulum (>=1.4,<2.0) ; (python_version ~= "2.7" and sys_platform =='
            ' "win32" or python_version in "3.4 3.5") and (extra == "time")'
        ),
    ]

    urls = parsed.get_all("Project-URL")
    assert urls == [
        "Documentation, https://python-poetry.org/docs",
        "Homepage, https://python-poetry.org/",
        "Issue Tracker, https://github.com/python-poetry/poetry/issues",
        "Repository, https://github.com/python-poetry/poetry",
    ]


def test_metadata_pretty_name() -> None:
    builder = Builder(
        Factory().create_poetry(Path(__file__).parent / "fixtures" / "Pretty.Name")
    )

    metadata = Parser().parsestr(builder.get_metadata_content())

    assert metadata["Name"] == "Pretty.Name"


def test_metadata_homepage_default() -> None:
    builder = Builder(
        Factory().create_poetry(Path(__file__).parent / "fixtures" / "simple_version")
    )

    metadata = Parser().parsestr(builder.get_metadata_content())

    assert metadata["Home-page"] is None


@pytest.mark.parametrize("license_type", ["file", "text", "str"])
def test_metadata_license_type_file(license_type: str) -> None:
    project_path = (
        Path(__file__).parent.parent.parent
        / "fixtures"
        / f"with_license_type_{license_type}"
    )
    builder = Builder(Factory().create_poetry(project_path))

    if license_type == "file":
        license_text = (project_path / "LICENSE").read_text(encoding="utf-8")
    elif license_type == "text":
        license_text = (
            (project_path / "pyproject.toml")
            .read_text(encoding="utf-8")
            .split('"""')[1]
        )
    elif license_type == "str":
        license_text = "MIT"
    else:
        raise RuntimeError("unexpected license type")

    raw_content = builder.get_metadata_content()
    metadata = Parser().parsestr(raw_content)

    license_lines = metadata["License"].splitlines()
    unindented_license = "\n".join([line.strip() for line in license_lines])
    assert unindented_license == license_text.rstrip()

    # Check that field after "license" is read correctly
    assert raw_content.index("License:") < raw_content.index("Keywords:")
    assert metadata["Keywords"] == "special"


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
        requires_dist == "demo @"
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

    assert "is not found." in str(err.value)


def test_invalid_script_files_definition() -> None:
    with pytest.raises(RuntimeError) as err:
        Builder(
            Factory().create_poetry(
                Path(__file__).parent
                / "fixtures"
                / "script_reference_file_invalid_definition"
            )
        )

    assert "configuration is invalid" in str(err.value)
    assert "scripts.invalid_definition" in str(err.value)


@pytest.mark.parametrize(
    "fixture, result",
    [
        (
            "script_callable_legacy_string",
            {"console_scripts": ["script-legacy = my_package:main"]},
        ),
        (
            "script_reference_console",
            {
                "console_scripts": [
                    "extra-script = my_package.extra:main",
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
    description = "\n".join(
        [readme1.read_text(encoding="utf-8"), readme2.read_text(encoding="utf-8"), ""]
    )

    assert metadata.get_payload() == description


def test_metadata_with_wildcard_dependency_constraint() -> None:
    test_path = (
        Path(__file__).parent / "fixtures" / "with_wildcard_dependency_constraint"
    )
    builder = Builder(Factory().create_poetry(test_path))

    metadata = Parser().parsestr(builder.get_metadata_content())

    requires = metadata.get_all("Requires-Dist")
    assert requires == ["google-api-python-client (>=1.8,!=2.0.*)"]


@pytest.mark.parametrize(
    ["local_version", "expected_version"],
    [
        ("", "1.2.3"),
        ("some-label", "1.2.3+some-label"),
    ],
)
def test_builder_apply_local_version_label(
    local_version: str, expected_version: str
) -> None:
    builder = Builder(
        Factory().create_poetry(Path(__file__).parent / "fixtures" / "complete"),
        config_settings={"local-version": local_version},
    )

    assert builder._poetry.package.version.text == expected_version
