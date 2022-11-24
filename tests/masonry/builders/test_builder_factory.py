from __future__ import annotations

import shutil

from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Iterator

import pytest

from poetry.core.factory import Factory
from poetry.core.masonry.builder import Builder


if TYPE_CHECKING:
    from poetry.core.poetry import Poetry


def get_project(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / name


@contextmanager
def get_project_context(name: str) -> Iterator[Path]:
    project_directory = get_project(name)
    try:
        yield project_directory
    finally:
        shutil.rmtree(project_directory / "dist")


def get_poetry(name: str) -> Poetry:
    return Factory().create_poetry(get_project(name))


def get_package_glob(poetry: Poetry) -> str:
    return f"{poetry.package.name.replace('-', '_')}-{poetry.package.version}*"


def test_builder_factory_raises_error_when_format_is_not_valid() -> None:
    with pytest.raises(ValueError, match=r"Invalid format.*"):
        Builder(get_poetry("complete")).build("not_valid")


@pytest.mark.parametrize("format", ["sdist", "wheel", "all"])
def test_builder_creates_places_built_files_in_specified_directory(
    tmp_path: Path, format: str
) -> None:
    poetry = get_poetry("complete")
    Builder(poetry).build(format, target_dir=tmp_path)
    assert all(archive.exists() for archive in tmp_path.glob(get_package_glob(poetry)))


@pytest.mark.parametrize("format", ["sdist", "wheel", "all"])
def test_builder_creates_packages_in_dist_directory_if_no_output_is_specified(
    format: str,
) -> None:
    with get_project_context("complete") as project:
        poetry = Factory().create_poetry(project)
        Builder(poetry).build(format, target_dir=None)
        package_directory = project / "dist"
        assert package_directory.is_dir()
        assert all(
            archive.exists()
            for archive in package_directory.glob(get_package_glob(poetry))
        )
