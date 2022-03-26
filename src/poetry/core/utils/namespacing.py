from __future__ import annotations

from pathlib import Path
from typing import Union


def extract_namespace(path: Path, workspace: Path) -> Union[str, None]:
    grandparent = path.parent.parent

    return grandparent.name if len(grandparent.relative_to(workspace).name) else None


def create_namespaced_path(path: Path, workspace: Path) -> Path:
    namespace = extract_namespace(path, workspace) or ""
    package_name = path.parent.name
    module_name = path.name

    namespaced_path = "/".join([namespace, package_name, module_name])

    return Path(namespaced_path)
