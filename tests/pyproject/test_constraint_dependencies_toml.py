from urllib.error import URLError

import pytest

from poetry.core.pyproject.constraint_dependencies_toml import (
    ConstraintDependenciesTOML,
)


@pytest.mark.parametrize(
    "path_or_url,url",
    [
        ("constraints.toml", "file:constraints.toml"),
        ("file:constraints.toml", "file:constraints.toml"),
        ("file:///constraints.toml", "file:///constraints.toml"),
        ("http://example.com/constraints.toml", "http://example.com/constraints.toml"),
        (
            "https://example.com/constraints.toml",
            "https://example.com/constraints.toml",
        ),
    ],
)
def test_constraints(mocker, path_or_url, url):
    mock_response = mocker.Mock()
    mock_response.read.return_value = b"""[poetry.constraint-dependencies]
cleo = "0.7"
"""
    mock_urlopen = mocker.patch("urllib.request.urlopen")
    mock_urlopen.return_value = mock_response

    toml = ConstraintDependenciesTOML(path_or_url)
    constraints = toml.dependencies

    assert constraints["cleo"] == "0.7"
    mock_urlopen.assert_called_once_with(url)


def test_constraints_url_error(mocker):
    url_error = URLError("forced failure")
    mocker.patch("urllib.request.urlopen").side_effect = url_error

    toml = ConstraintDependenciesTOML("constraints.toml")

    with pytest.raises(
        RuntimeError,
        match=r"Poetry could not load constraint dependencies file constraints\.toml",
    ) as e:
        constraints = toml.dependencies

    assert e.value.__cause__ == url_error


def test_constraints_key_error(mocker):
    from tomlkit.exceptions import NonExistentKey

    mock_response = mocker.Mock()
    mock_response.read.return_value = b""
    mock_urlopen = mocker.patch("urllib.request.urlopen")
    mock_urlopen.return_value = mock_response

    toml = ConstraintDependenciesTOML("constraints.toml")

    with pytest.raises(
        RuntimeError,
        match=r"\[poetry.constraint-dependencies\] section not found in constraints\.toml",
    ) as e:
        constraints = toml.dependencies

    assert type(e.value.__cause__) == NonExistentKey
