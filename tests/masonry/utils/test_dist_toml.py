from __future__ import annotations

import tomlkit

from poetry.core.masonry.utils.dist_toml import to_valid_dist_package
from poetry.core.masonry.utils.dist_toml import to_valid_dist_packages


def test_to_valid_dist_package() -> None:
    content = """
    [tool.poetry]
    packages = [{"include" = "foo/bar", from = "../../components"}]
    """
    data = tomlkit.parse(content)

    package = data["tool"]["poetry"]["packages"][0]

    res = to_valid_dist_package(package)

    assert res == {"include": "foo/bar"}


def test_to_valid_dist_package_without_relative_include() -> None:
    content = """
    [tool.poetry]
    packages = [{"include" = "foo", from = "bar"}]
    """
    data = tomlkit.parse(content)

    package = data["tool"]["poetry"]["packages"][0]

    res = to_valid_dist_package(package)

    assert res == {"include": "foo", "from": "bar"}


def test_to_valid_dist_packages() -> None:
    content = """
    [tool.poetry]
    packages = [{"include" = "foo/bar", from = "../../components"}]
    """
    data = tomlkit.parse(content)

    res = to_valid_dist_packages(data)

    assert res == [{"include": "foo/bar"}]


def test_to_valid_dist_packages_with_mixed_includes() -> None:
    content = """
    [tool.poetry]
    packages = [
       {"include" = "foo/bar", from = "../../components"},
       {"include" = "foo", from = "bar"}
    ]
    """
    data = tomlkit.parse(content)

    res = to_valid_dist_packages(data)

    assert res == [{"include": "foo/bar"}, {"include": "foo", "from": "bar"}]
