import pytest

from poetry.core.pyproject import PyProjectException
from poetry.core.pyproject import PyProjectTOMLFile
from poetry.core.utils._compat import decode
from poetry.core.utils.toml_file import TomlFile


def test_old_pyproject_toml_file_deprecation(
    pyproject_toml, build_system_section, poetry_section
):
    with pytest.warns(DeprecationWarning):
        file = TomlFile(pyproject_toml)

    data = file.read()
    assert data == PyProjectTOMLFile(pyproject_toml).read()


def test_pyproject_toml_file_invalid(pyproject_toml):
    with pyproject_toml.open(mode="a") as f:
        f.write(decode("<<<<<<<<<<<"))

    with pytest.raises(PyProjectException) as excval:
        _ = PyProjectTOMLFile(pyproject_toml).read()

    assert "Invalid TOML file {}".format(pyproject_toml.as_posix()) in str(excval.value)


def test_pyproject_toml_file_getattr(tmp_path, pyproject_toml):
    file = PyProjectTOMLFile(pyproject_toml)
    assert file.parent == tmp_path
