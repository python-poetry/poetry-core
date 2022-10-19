from pathlib import Path


from poetry.core.masonry.builders.builder import BuildIncludeFile


def test_path_is_relative_to_workspace() -> None:
    expected = "components/foo/bar.py"

    path = Path(f"workspace/{expected}").resolve()
    project_root = Path("workspace/projects/my_project").resolve()
    source_root = None
    workspace = Path("workspace").resolve()

    bif = BuildIncludeFile(path, project_root, source_root, workspace)

    assert bif.relative_to_workspace() == Path(expected)


def test_relative_path_with_source_root_is_relative_to_workspace() -> None:
    expected = "components/foo/bar.py"

    project_root = Path("workspace/projects/my_project").resolve()
    source_root = Path("workspace").resolve()
    workspace = Path("workspace").resolve()

    bif = BuildIncludeFile(expected, project_root, source_root, workspace)

    assert bif.relative_to_workspace() == Path(expected)


def test_path_is_relative_to_workspace_when_not_in_workspace() -> None:
    path = Path("my_repo/my_app/foo/bar.py").resolve()
    project_root = Path("my_repo").resolve()
    source_root = None
    workspace = None

    bif = BuildIncludeFile(path, project_root, source_root, workspace)

    assert bif.relative_to_workspace() == path
