from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tomlkit


def to_valid_dist_package(package: dict[str, str]) -> dict[str, str]:
    """Returns a [tool.poetry] packages list item.

    Rearranges the "include" and "from" attributes for relative included packages,
    adapting to the sdist build output.

    The output from this function will reflect the build output to:
    {"include": "foo/bar"}
    """
    if ".." not in package.get("from", ""):
        return package

    return {"include": package["include"]}


def to_valid_dist_packages(data: tomlkit.toml.TOMLDocument) -> list[dict[str, str]]:
    """Returns a [tool.poetry] packages section.

    Rearrange packages with relative paths, to reflect the sdist build output.

    Example: a pyproject.toml with relative packages.
    packages = [{"include": "foo/bar", from: "../../components"}]

    When building an sdist (using the "poetry build" command),
    the packages will be collected and copied into a local directory.
    /dist
      /setup.py
      /foo/bar

    The end result in a toml file from running this function would be:
    packages = [{"include" = "foo/bar"}]
    """
    packages = data["tool"]["poetry"]["packages"]

    return [to_valid_dist_package(p) for p in packages]
