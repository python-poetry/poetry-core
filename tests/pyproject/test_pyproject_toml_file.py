import pytest

from poetry.core.exceptions import PoetryCoreException
from poetry.core.toml import TOMLFile


def test_old_pyproject_toml_file_deprecation(
    pyproject_toml, build_system_section, poetry_section
):
    from poetry.core.utils.toml_file import TomlFile

    with pytest.warns(DeprecationWarning):
        file = TomlFile(pyproject_toml)

    data = file.read()
    assert data == TOMLFile(pyproject_toml).read()


def test_pyproject_toml_file_invalid(pyproject_toml):
    with pyproject_toml.open(mode="a") as f:
        f.write("<<<<<<<<<<<")

    with pytest.raises(PoetryCoreException) as excval:
        _ = TOMLFile(pyproject_toml).read()

    assert "Invalid TOML file {}".format(pyproject_toml.as_posix()) in str(excval.value)


def test_pyproject_toml_file_getattr(tmp_path, pyproject_toml):
    file = TOMLFile(pyproject_toml)
    assert file.parent == tmp_path
