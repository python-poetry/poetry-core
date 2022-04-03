from __future__ import annotations

from pathlib import Path


workspace_file = "workspace.toml"


def is_repo_root(cwd: Path) -> bool:
    fullpath = cwd / ".git"

    return fullpath.exists()


def find_upwards(cwd: Path, name: str) -> Path | None:
    if cwd == Path(cwd.root):
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
    return find_upwards_dir(cwd, workspace_file)
