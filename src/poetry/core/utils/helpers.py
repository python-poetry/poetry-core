from __future__ import annotations

import os
import shutil
import stat
import tempfile
import time
import unicodedata
import warnings

from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from packaging.utils import canonicalize_name

from poetry.core.version.pep440 import PEP440Version


if TYPE_CHECKING:
    from collections.abc import Iterator


def combine_unicode(string: str) -> str:
    return unicodedata.normalize("NFC", string)


def module_name(name: str) -> str:
    return canonicalize_name(name).replace("-", "_")


def normalize_version(version: str) -> str:
    warnings.warn(
        "normalize_version() is deprecated. Use Version.parse().to_string() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return PEP440Version.parse(version).to_string()


@contextmanager
def temporary_directory(*args: Any, **kwargs: Any) -> Iterator[str]:
    name = tempfile.mkdtemp(*args, **kwargs)
    yield name
    robust_rmtree(name)


def parse_requires(requires: str) -> list[str]:
    lines = requires.split("\n")

    requires_dist = []
    current_marker = None
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("["):
            # extras or conditional dependencies
            marker = line.lstrip("[").rstrip("]")
            if ":" not in marker:
                extra, marker = marker, ""
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


def robust_rmtree(path: str, max_timeout: float = 1) -> None:
    """
    Robustly tries to delete paths.
    Retries several times if an OSError occurs.
    If the final attempt fails, the Exception is propagated
    to the caller.
    """
    timeout = 0.001
    while timeout < max_timeout:
        try:
            # both os.unlink and shutil.rmtree can throw exceptions on Windows
            # if the files are in use when called
            if Path(path).is_symlink():
                os.unlink(str(path))
            else:
                shutil.rmtree(path)
            return  # Only hits this on success
        except OSError:
            # Increase the timeout and try again
            time.sleep(timeout)
            timeout *= 2

    # Final attempt, pass any Exceptions up to caller.
    shutil.rmtree(path, onerror=_on_rm_error)


def readme_content_type(path: str | Path) -> str:
    suffix = Path(path).suffix
    if suffix == ".rst":
        return "text/x-rst"
    elif suffix in (".md", ".markdown"):
        return "text/markdown"
    else:
        return "text/plain"
