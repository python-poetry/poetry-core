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
