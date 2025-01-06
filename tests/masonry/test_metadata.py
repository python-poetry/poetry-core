from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from poetry.core.masonry.metadata import Metadata
from poetry.core.packages.project_package import ProjectPackage


if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_from_package_readme(tmp_path: Path) -> None:
    readme_path = tmp_path / "README.md"
    readme_path.write_text("This is a description\néöß", encoding="utf-8")

    package = ProjectPackage("foo", "1.0")
    package.readmes = (readme_path,)

    metadata = Metadata.from_package(package)

    assert metadata.description == "This is a description\néöß"


def test_from_package_multiple_readmes(tmp_path: Path) -> None:
    readme_path1 = tmp_path / "README1.md"
    readme_path1.write_text("Description 1", encoding="utf-8")

    readme_path2 = tmp_path / "README2.md"
    readme_path2.write_text("Description 2", encoding="utf-8")

    package = ProjectPackage("foo", "1.0")
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
    mocker: MockerFixture, exception: type[OSError], message: str
) -> None:
    package = ProjectPackage("foo", "1.0")
    package.readmes = (Path("MyReadme.md"),)

    mocker.patch("pathlib.Path.read_text", side_effect=exception)

    with pytest.raises(exception) as e:
        Metadata.from_package(package)

    assert str(e.value) == message


def test_from_package_urls_case_sensitive() -> None:
    package = ProjectPackage("foo", "1.0")
    package.homepage = "https://example.com"
    package._urls = {
        "Homepage": "https://example.com",
        "Repository": "https://github.com/example/repo",
        "Documentation": "https://docs.example.com",
        "Other": "https://other.example.com",
    }

    metadata = Metadata.from_package(package)

    # Only "Other" should be in project_urls since others are special cases
    assert len(metadata.project_urls) == 1
    assert metadata.project_urls[0] == "Other, https://other.example.com"


def test_from_package_urls_case_mixed() -> None:
    package = ProjectPackage("foo", "1.0")
    package.homepage = "https://example.com"
    package._urls = {
        "homepage": "https://example.com",
        "Repository": "https://github.com/example/repo",
        "DOCUMENTATION": "https://docs.example.com",
        "other": "https://other.example.com",
    }

    metadata = Metadata.from_package(package)

    # Only "other" should be in project_urls since others are special cases
    assert len(metadata.project_urls) == 1
    assert metadata.project_urls[0] == "other, https://other.example.com"


def test_from_package_urls_lowercase() -> None:
    package = ProjectPackage("foo", "1.0")
    package._urls = {
        "homepage": "https://example.com",
        "repository": "https://github.com/example/repo",
        "documentation": "https://docs.example.com",
        "other": "https://other.example.com",
    }

    metadata = Metadata.from_package(package)

    # Only "other" should be in project_urls since others are special cases
    assert len(metadata.project_urls) == 2
    assert metadata.project_urls[0] == "homepage, https://example.com"
    assert metadata.project_urls[1] == "other, https://other.example.com"
