from __future__ import annotations

from pathlib import Path

from poetry.core.masonry.builders.builder import BuildIncludeFile


ws_path = "my_workspace"


def test_path_is_relative_to_workspace() -> None:
    expected = "components/foo/bar.py"

    path = Path(f"{ws_path}/{expected}").resolve()
    project_root = Path(f"{ws_path}/projects/my_project").resolve()
    workspace = Path(ws_path).resolve()

    bif = BuildIncludeFile(path, project_root, None, workspace)

    assert bif.relative_to_workspace() == Path(expected)


def test_path_is_relative_to_workspace_when_not_in_workspace() -> None:
    path = Path("my_repo/my_app/foo/bar.py").resolve()
    project_root = Path("my_repo").resolve()

    bif = BuildIncludeFile(path, project_root, None, None)

    assert bif.relative_to_workspace() == path


def test_calculated_path() -> None:
    expected = "components/foo/bar.py"

    path = Path(f"{ws_path}/{expected}").resolve()
    project_root = Path(f"{ws_path}/projects/my_project").resolve()
    workspace = Path(ws_path).resolve()

    bif = BuildIncludeFile(path, project_root, None, workspace)

    assert bif.calculated_path() == Path(expected)


def test_calculated_path_when_not_in_workspace() -> None:
    path = Path("my_repo/my_app/foo/bar.py").resolve()
    project_root = Path("my_repo").resolve()

    bif = BuildIncludeFile(path, project_root, None, None)

    assert bif.calculated_path() == path
