from pathlib import Path
import pytest
from poetry.core.masonry.builder import Builder
from poetry.core.factory import Factory


def project(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / name


def get_poetry(name: str):
    return Factory().create_poetry(project(name))


def test_builder_factory_raises_error_when_format_is_not_valid():
    with pytest.raises(ValueError, match=r"Invalid format.*"):
        Builder(get_poetry("complete")).build("not_valid")


@pytest.mark.parametrize("format", ["sdist", "wheel", "all"])
def test_builder_creates_new_directory(tmp_path: Path, format: str):
    poetry = Factory().create_poetry(Path(__file__).parent / "fixtures" / "complete")
    Builder(poetry).build(format, tmp_path)
    assert all(archive.exists() for archive in tmp_path.glob(
        f"{poetry.package.name.replace('-', '_')}-{poetry.package.version}*"))
