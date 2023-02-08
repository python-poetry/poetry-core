from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from poetry.core.exceptions import PoetryCoreException
from poetry.core.toml import TOMLFile


if TYPE_CHECKING:
    from pathlib import Path


def test_old_pyproject_toml_file_deprecation(
    pyproject_toml: Path, build_system_section: str, poetry_section: str
) -> None:
    from poetry.core.utils.toml_file import TomlFile

    with pytest.warns(DeprecationWarning):
        file = TomlFile(pyproject_toml)

    data = file.read()
    assert data == TOMLFile(pyproject_toml).read()


def test_pyproject_toml_file_invalid(pyproject_toml: Path) -> None:
    with pyproject_toml.open(mode="a") as f:
        f.write("<<<<<<<<<<<")

    with pytest.raises(PoetryCoreException) as excval:
        _ = TOMLFile(pyproject_toml).read()

    assert f"Invalid TOML file {pyproject_toml.as_posix()}" in str(excval.value)


def test_pyproject_toml_file_getattr(tmp_path: Path, pyproject_toml: Path) -> None:
    file = TOMLFile(pyproject_toml)
    assert file.parent == tmp_path
