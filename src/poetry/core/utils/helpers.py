from __future__ import annotations

import os
import shutil
import stat
import tempfile
import unicodedata
import warnings

from contextlib import contextmanager
from email.utils import parseaddr
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
    safe_rmtree(name)


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


def safe_rmtree(path: str | Path) -> None:
    if Path(path).is_symlink():
        return os.unlink(str(path))

    shutil.rmtree(path, onerror=_on_rm_error)


def readme_content_type(path: str | Path) -> str:
    suffix = Path(path).suffix
    if suffix == ".rst":
        return "text/x-rst"
    elif suffix in (".md", ".markdown"):
        return "text/markdown"
    else:
        return "text/plain"


def parse_author(address: str) -> tuple[str, str | None]:
    """Parse name and address parts from an email address string.

    >>> parse_author("John Doe <john.doe@example.com>")
    ('John Doe', 'john.doe@example.com')

    :param address: the email address string to parse.
    :return: a 2-tuple with the parsed name and optional email address.
    :raises ValueError: if the parsed string does not contain a name.
    """
    if "@" not in address:
        return address, None
    name, email = parseaddr(address)
    if not name or (
        email and address not in [f"{name} <{email}>", f'"{name}" <{email}>']
    ):
        raise ValueError(f"Invalid author string: {address!r}")
    return name, email or None
