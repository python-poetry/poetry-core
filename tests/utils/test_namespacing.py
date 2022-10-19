from __future__ import annotations

from pathlib import Path

from poetry.core.utils.namespacing import convert_to_namespace
from poetry.core.utils.namespacing import create_namespaced_path


def test_create_namespaced_path() -> None:
    expected = "my_namespace/my_package/my_module.py"

    path = Path(f"my_workspace/{expected}")
    workspace = Path("my_workspace")

    assert create_namespaced_path(path, workspace).as_posix() == expected


def test_convert_to_namespace() -> None:
    assert convert_to_namespace("foo/bar") == "foo.bar"
