from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from packaging.licenses import canonicalize_license_expression

from poetry.core.masonry.metadata import Metadata
from poetry.core.packages.project_package import ProjectPackage
from poetry.core.spdx.helpers import license_by_id


if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture
def package(tmp_path: Path) -> ProjectPackage:
    package = ProjectPackage("foo", "1.0")
    package.root_dir = tmp_path
    return package


@pytest.fixture
def default_license_files(tmp_path: Path) -> tuple[str, ...]:
    # everything that is covered by our default handling
    license_files = (
        "AUTHORS",
        "AUTHORS1",
        "COPYING",
        "COPYING1",
        "LICENCE",
        "LICENCE1",
        "LICENSE",
        "LICENSE1",
        "LICENSES/FILE1",
        "LICENSES/FILE2",
        "LICENSES/sub/FILE",
        "NOTICE",
        "NOTICE1",
    )
    for file in license_files:
        path = tmp_path / file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

        # subdirectory that should not be covered
        path = tmp_path / "sub" / file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    # a directory which should not be covered
    (tmp_path / "LICENSE2").mkdir()

    return license_files


@pytest.mark.parametrize(
    ("requires_python", "python", "expected"),
    [
        (">=3.8", None, ">=3.8"),
        (None, "^3.8", ">=3.8,<4.0"),
        (">=3.8", "^3.8", ">=3.8"),
    ],
)
def test_from_package_requires_python(
    package: ProjectPackage,
    requires_python: str | None,
    python: str | None,
    expected: str,
) -> None:
    if requires_python:
        package.requires_python = requires_python
    if python:
        package.python_versions = python

    meta = Metadata.from_package(package)

    assert meta.requires_python == expected


@pytest.mark.parametrize(
    "license",
    [None, "MIT", "Apache-2.0 OR BSD-2-Clause", "LicenseRef-MyProprietaryLicense"],
)
def test_from_package_license_expression(
    package: ProjectPackage, license: str | None
) -> None:
    if license:
        package.license_expression = canonicalize_license_expression(license)

    metadata = Metadata.from_package(package)

    assert metadata.license_expression == license
    assert metadata.license is None


def test_from_package_license(package: ProjectPackage) -> None:
    package.license = license_by_id("MIT")

    metadata = Metadata.from_package(package)

    assert metadata.license_expression is None
    assert metadata.license == "MIT"


def test_from_package_license_files_not_set_no_files(package: ProjectPackage) -> None:
    package.license_files = None

    metadata = Metadata.from_package(package)

    assert metadata.license_files == ()


def test_from_package_license_files_not_set_default_files(
    package: ProjectPackage, default_license_files: tuple[str, ...]
) -> None:
    package.license_files = None

    metadata = Metadata.from_package(package)

    assert metadata.license_files == default_license_files


def test_from_package_license_files_explicitly_no_files(
    package: ProjectPackage, default_license_files: tuple[str, ...]
) -> None:
    package.license_files = ()

    metadata = Metadata.from_package(package)

    assert metadata.license_files == ()


def test_from_package_license_files_path(package: ProjectPackage) -> None:
    package.license_files = Path("sub", "LICENSE")
    assert package.root_dir
    (package.root_dir / package.license_files).parent.mkdir()
    (package.root_dir / package.license_files).touch()

    metadata = Metadata.from_package(package)

    assert metadata.license_files == ("sub/LICENSE",)


def test_from_package_license_files_path_and_default_files(
    package: ProjectPackage, default_license_files: tuple[str, ...]
) -> None:
    package.license_files = Path("sub", "LICENSE")

    metadata = Metadata.from_package(package)

    assert metadata.license_files == (*default_license_files, "sub/LICENSE")


def test_from_package_license_files_glob_patterns(
    package: ProjectPackage, default_license_files: tuple[str, ...]
) -> None:
    package.license_files = ("sub/**/*", "**/LICENSE")

    metadata = Metadata.from_package(package)

    assert metadata.license_files == (
        "LICENSE",
        *[f"sub/{f}" for f in default_license_files],
    )


def test_from_package_license_files_no_file_for_pattern(
    package: ProjectPackage, default_license_files: tuple[str, ...]
) -> None:
    package.license_files = ("COPYING*", "foo/*", "**/LICENSE")

    with pytest.raises(RuntimeError) as e:
        Metadata.from_package(package)
    assert str(e.value) == "No files found for license file glob pattern 'foo/*'"


def test_from_package_readme(package: ProjectPackage) -> None:
    assert package.root_dir
    readme_path = package.root_dir / "README.md"
    readme_path.write_text("This is a description\néöß", encoding="utf-8")

    package.readmes = (readme_path,)

    metadata = Metadata.from_package(package)

    assert metadata.description == "This is a description\néöß"


def test_from_package_multiple_readmes(package: ProjectPackage) -> None:
    assert package.root_dir
    readme_path1 = package.root_dir / "README1.md"
    readme_path1.write_text("Description 1", encoding="utf-8")

    readme_path2 = package.root_dir / "README2.md"
    readme_path2.write_text("Description 2", encoding="utf-8")

    package.readmes = (readme_path1, readme_path2)

    metadata = Metadata.from_package(package)

    assert metadata.description == "Description 1\nDescription 2"


@pytest.mark.parametrize(
    ("exception", "message"),
    [
        (FileNotFoundError, "Readme path `MyReadme.md` does not exist."),
        (IsADirectoryError, "Readme path `MyReadme.md` is a directory."),
        (PermissionError, "Readme path `MyReadme.md` is not readable."),
    ],
)
def test_from_package_readme_issues(
    package: ProjectPackage,
    mocker: MockerFixture,
    exception: type[OSError],
    message: str,
) -> None:
    package.readmes = (Path("MyReadme.md"),)

    mocker.patch("pathlib.Path.read_text", side_effect=exception)

    with pytest.raises(exception) as e:
        Metadata.from_package(package)

    assert str(e.value) == message
