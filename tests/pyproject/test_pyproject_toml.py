import uuid

from pathlib import Path  # noqa

import pytest

from tomlkit.toml_document import TOMLDocument
from tomlkit.toml_file import TOMLFile

from poetry.core.pyproject.exceptions import PyProjectException
from poetry.core.pyproject.toml import PyProjectTOML


def test_pyproject_toml_simple(pyproject_toml, build_system_section, poetry_section):
    data = TOMLFile(pyproject_toml.as_posix()).read()
    assert PyProjectTOML(pyproject_toml).data == data


def test_pyproject_toml_no_poetry_config(pyproject_toml):
    pyproject = PyProjectTOML(pyproject_toml)

    assert not pyproject.is_poetry_project()

    with pytest.raises(PyProjectException) as excval:
        _ = pyproject.poetry_config

    assert "[tool.poetry] section not found in {}".format(
        pyproject_toml.as_posix()
    ) in str(excval.value)


def test_pyproject_toml_poetry_config(pyproject_toml, poetry_section):
    pyproject = PyProjectTOML(pyproject_toml)
    config = TOMLFile(pyproject_toml.as_posix()).read()["tool"]["poetry"]

    assert pyproject.is_poetry_project()
    assert pyproject.poetry_config == config


def test_pyproject_toml_no_build_system_defaults():
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


def test_pyproject_toml_build_requires_as_dependencies(pyproject_toml):
    build_system = PyProjectTOML(pyproject_toml).build_system
    assert build_system.requires == ["setuptools", "wheel"]
    assert build_system.build_backend == "setuptools.build_meta:__legacy__"


def test_pyproject_toml_non_existent(pyproject_toml):
    pyproject_toml.unlink()
    pyproject = PyProjectTOML(pyproject_toml)
    build_system = pyproject.build_system

    assert pyproject.data == TOMLDocument()
    assert build_system.requires == ["poetry-core"]
    assert build_system.build_backend == "poetry.core.masonry.api"


def test_pyproject_toml_reload(pyproject_toml, poetry_section):
    pyproject = PyProjectTOML(pyproject_toml)
    name_original = pyproject.poetry_config["name"]
    name_new = str(uuid.uuid4())

    pyproject.poetry_config["name"] = name_new
    assert pyproject.poetry_config["name"] == name_new

    pyproject.reload()
    assert pyproject.poetry_config["name"] == name_original


def test_pyproject_toml_save(pyproject_toml, poetry_section, build_system_section):
    pyproject = PyProjectTOML(pyproject_toml)

    name = str(uuid.uuid4())
    build_backend = str(uuid.uuid4())
    build_requires = str(uuid.uuid4())

    pyproject.poetry_config["name"] = name
    pyproject.build_system.build_backend = build_backend
    pyproject.build_system.requires.append(build_requires)

    pyproject.save()

    pyproject = PyProjectTOML(pyproject_toml)

    assert pyproject.poetry_config["name"] == name
    assert pyproject.build_system.build_backend == build_backend
    assert build_requires in pyproject.build_system.requires
