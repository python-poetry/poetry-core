from __future__ import annotations

from pathlib import Path

import pytest

from poetry.core.pyproject.exceptions import PyProjectError
from poetry.core.pyproject.toml import PyProjectTOML
from poetry.core.utils._compat import tomllib


def test_pyproject_toml_simple(
    pyproject_toml: Path, build_system_section: str, poetry_section: str
) -> None:
    with pyproject_toml.open("rb") as f:
        data = tomllib.load(f)
    assert PyProjectTOML(pyproject_toml).data == data


def test_pyproject_toml_no_poetry_config(pyproject_toml: Path) -> None:
    pyproject = PyProjectTOML(pyproject_toml)

    assert not pyproject.is_poetry_project()

    with pytest.raises(PyProjectError) as excval:
        _ = pyproject.poetry_config

    assert f"[tool.poetry] section not found in {pyproject_toml.as_posix()}" in str(
        excval.value
    )


def test_pyproject_toml_no_poetry_config_but_project_section(
    pyproject_toml: Path, project_section: str
) -> None:
    pyproject = PyProjectTOML(pyproject_toml)

    assert pyproject.is_poetry_project()

    with pytest.raises(PyProjectError) as excval:
        _ = pyproject.poetry_config

    assert f"[tool.poetry] section not found in {pyproject_toml.as_posix()}" in str(
        excval.value
    )


def test_pyproject_toml_no_poetry_config_but_project_section_but_dynamic(
    pyproject_toml: Path, project_section_dynamic: str
) -> None:
    pyproject = PyProjectTOML(pyproject_toml)

    assert not pyproject.is_poetry_project()

    with pytest.raises(PyProjectError) as excval:
        _ = pyproject.poetry_config

    assert f"[tool.poetry] section not found in {pyproject_toml.as_posix()}" in str(
        excval.value
    )


def test_pyproject_toml_poetry_config(
    pyproject_toml: Path, poetry_section: str
) -> None:
    pyproject = PyProjectTOML(pyproject_toml)
    with pyproject_toml.open("rb") as f:
        doc = tomllib.load(f)
    config = doc["tool"]["poetry"]

    assert pyproject.is_poetry_project()
    assert pyproject.poetry_config == config


def test_pyproject_toml_no_build_system_defaults() -> None:
    pyproject_toml = (
        Path(__file__).parent.parent
        / "fixtures"
        / "project_with_build_system_requires"
        / "pyproject.toml"
    )

    build_system = PyProjectTOML(pyproject_toml).build_system
    assert build_system.requires == ["poetry-core", "Cython~=0.29.6"]

    assert len(build_system.dependencies) == 2
    assert build_system.dependencies[0].to_pep_508() == "poetry-core"
    assert build_system.dependencies[1].to_pep_508() == "Cython (>=0.29.6,<0.30.0)"


def test_pyproject_toml_build_requires_as_dependencies(pyproject_toml: Path) -> None:
    build_system = PyProjectTOML(pyproject_toml).build_system
    assert build_system.requires == ["setuptools", "wheel"]
    assert build_system.build_backend == "setuptools.build_meta:__legacy__"


def test_pyproject_toml_non_existent(pyproject_toml: Path) -> None:
    pyproject_toml.unlink()
    pyproject = PyProjectTOML(pyproject_toml)
    build_system = pyproject.build_system

    assert pyproject.data == {}
    assert build_system.requires == ["poetry-core"]
    assert build_system.build_backend == "poetry.core.masonry.api"


def test_unparseable_pyproject_toml() -> None:
    pyproject_toml = (
        Path(__file__).parent.parent
        / "fixtures"
        / "project_duplicate_dependency"
        / "pyproject.toml"
    )

    with pytest.raises(PyProjectError) as excval:
        _ = PyProjectTOML(pyproject_toml).build_system

    assert (
        f"{pyproject_toml.as_posix()} is not a valid TOML file.\n"
        "TOMLDecodeError: Cannot overwrite a value (at line 7, column 16)\n"
        "This is often caused by a duplicate entry"
    ) in str(excval.value)
