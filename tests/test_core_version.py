from __future__ import annotations

from pathlib import Path

from poetry.core import __version__
from poetry.core.pyproject.formats.content_format import ContentFormat
from poetry.core.pyproject.toml import PyProjectTOML


def test_version_is_synced() -> None:
    pyproject = PyProjectTOML(Path(__file__).parent.parent.joinpath("pyproject.toml"))
    content_format = pyproject.content_format
    assert isinstance(content_format, ContentFormat)
    assert __version__ == content_format.to_package(pyproject.path).version.text
