from pathlib import Path

import pytest


@pytest.fixture
def pyproject_toml(tmp_path):  # type: (Path) -> Path
    path = tmp_path / "pyproject.toml"
    with path.open(mode="w"):
        pass
    return path


@pytest.fixture
def build_system_section(pyproject_toml):  # type: (Path) -> str
    content = """
[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""
    with pyproject_toml.open(mode="a") as f:
        f.write(content)
    return content


@pytest.fixture
def poetry_section(pyproject_toml):  # type: (Path) -> str
    content = """
[tool.poetry]
name = "poetry"

[tool.poetry.dependencies]
python = "^3.5"
"""
    with pyproject_toml.open(mode="a") as f:
        f.write(content)
    return content
