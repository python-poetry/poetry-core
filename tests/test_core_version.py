from __future__ import annotations

from pathlib import Path

from poetry.core import __version__
from poetry.core.pyproject.toml import PyProjectTOML


def test_version_is_synced() -> None:
    pyproject = PyProjectTOML(Path(__file__).parent.parent.joinpath("pyproject.toml"))
    assert __version__ == pyproject.poetry_config.get("version")
