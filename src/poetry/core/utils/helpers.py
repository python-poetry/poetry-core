from __future__ import annotations

import os
import re
import shutil
import stat
import tempfile
import unicodedata

from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from typing import Iterator
from typing import no_type_check

from poetry.core.version.pep440 import PEP440Version


_canonicalize_regex = re.compile(r"[-_.]+")


def combine_unicode(string: str) -> str:
    return unicodedata.normalize("NFC", string)


def canonicalize_name(name: str) -> str:
    return _canonicalize_regex.sub("-", name).lower()


def module_name(name: str) -> str:
    return canonicalize_name(name).replace(".", "_").replace("-", "_")


def normalize_version(version: str) -> str:
    return PEP440Version.parse(version).to_string()


@contextmanager
def temporary_directory(*args: Any, **kwargs: Any) -> Iterator[str]:
    name = tempfile.mkdtemp(*args, **kwargs)
    yield name
    safe_rmtree(name)


@no_type_check
def parse_requires(requires: str) -> list[str]:
    lines = requires.split("\n")

    requires_dist = []
    in_section = False
    current_marker = None
    for line in lines:
        line = line.strip()
        if not line:
            if in_section:
                in_section = False

            continue

        if line.startswith("["):
            # extras or conditional dependencies
            marker = line.lstrip("[").rstrip("]")
            if ":" not in marker:
                extra, marker = marker, None
            else:
                extra, marker = marker.split(":")

            if extra:
                if marker:
                    marker = f'{marker} and extra == "{extra}"'
                else:
                    marker = f'extra == "{extra}"'

            if marker:
                current_marker = marker

            continue

        if current_marker:
            line = f"{line} ; {current_marker}"

        requires_dist.append(line)

    return requires_dist


def _on_rm_error(func: Any, path: str | Path, exc_info: Any) -> None:
    if not os.path.exists(path):
        return

    os.chmod(path, stat.S_IWRITE)
    func(path)


def safe_rmtree(path: str | Path) -> None:
    if Path(path).is_symlink():
        return os.unlink(str(path))

    shutil.rmtree(path, onerror=_on_rm_error)


def merge_dicts(d1: dict[Any, Any], d2: dict[Any, Any]) -> None:
    for k in d2.keys():
        if k in d1 and isinstance(d1[k], dict) and isinstance(d2[k], Mapping):
            merge_dicts(d1[k], d2[k])
        else:
            d1[k] = d2[k]


def readme_content_type(path: str | Path) -> str:
    suffix = Path(path).suffix
    if suffix == ".rst":
        return "text/x-rst"
    elif suffix in [".md", ".markdown"]:
        return "text/markdown"
    else:
        return "text/plain"
