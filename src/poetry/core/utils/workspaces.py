from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from poetry.core.toml import TOMLFile


if TYPE_CHECKING:
    import tomlkit


workspace_file = "workspace.toml"


def parse_workspace_toml(path: Path) -> tomlkit.toml.TOMLDocument:
    t = TOMLFile(path / workspace_file)

    return t.read()


def is_poetry_workspace(data: tomlkit.toml.TOMLDocument) -> bool:
    """Check if a workspace is a Poetry workspace

    Returns True when there is a [tool.poetry.workspace] in the workspace TOML,
    otherwise False.
    """
    try:
        data["tool"]["poetry"]["workspace"]
        return True
    except KeyError:
        return False


def is_drive_root(cwd: Path) -> bool:
    return cwd == Path(cwd.root) or cwd == cwd.parent


def is_repo_root(cwd: Path) -> bool:
    fullpath = cwd / ".git"

    return fullpath.exists()


def find_upwards(cwd: Path, name: str) -> Path | None:
    if is_drive_root(cwd):
        return None

    fullpath = cwd / name

    if fullpath.exists():
        return fullpath

    if is_repo_root(cwd):
        return None

    return find_upwards(cwd.parent, name)


def find_upwards_dir(cwd: Path, name: str) -> Path | None:
    fullpath = find_upwards(cwd, name)

    return fullpath.parent if fullpath else None


def find_workspace_root(cwd: Path) -> Path | None:
    """Find the workspace root path.

    Navigates upwards a drive directory to find a workspace identifier, if existing.
    """
    root = find_upwards_dir(cwd, workspace_file)

    if not root:
        return None

    data = parse_workspace_toml(root)

    return root if is_poetry_workspace(data) else None
