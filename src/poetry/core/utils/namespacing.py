from __future__ import annotations

from pathlib import Path


def extract_namespace(path: Path, workspace: Path) -> str | None:
    grandparent = path.parent.parent

    return grandparent.name if len(grandparent.relative_to(workspace).name) else None


def create_namespaced_path(path: Path, workspace: Path) -> Path:
    """Create a namespaced path for a package, relative to a workspace.

    Example:

    Given a workspace structure
    /workspace
       /components
         /foo
          /bar
           baz.py

    The input:
    path my_workspace/components/foo/bar/baz.py
    workspace components

    Returns: foo/bar/baz.py
    """
    namespace = extract_namespace(path, workspace) or ""
    package_name = path.parent.name
    module_name = path.name

    namespaced_path = "/".join([namespace, package_name, module_name])

    return Path(namespaced_path)


def convert_to_namespace(dirs: str) -> str:
    """Convert a directory path string to a Python namespace string

    Example: from foo/bar to foo.bar
    """
    parts = dirs.split("/")

    return ".".join(parts)
