from __future__ import annotations

import os
import posixpath
import re
import sys

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Dict
from typing import List
from typing import Tuple
from urllib.parse import unquote
from urllib.parse import urlsplit
from urllib.request import url2pathname

from poetry.core.semver.version_range import VersionRange
from poetry.core.version.markers import dnf


if TYPE_CHECKING:
    from poetry.core.packages.constraints import BaseConstraint
    from poetry.core.semver.version import Version
    from poetry.core.semver.version_constraint import VersionConstraint
    from poetry.core.semver.version_union import VersionUnion
    from poetry.core.version.markers import BaseMarker

    # Even though we've `from __future__ import annotations`, mypy doesn't seem to like
    # this as `dict[str, ...]`
    ConvertedMarkers = Dict[str, List[List[Tuple[str, str]]]]


BZ2_EXTENSIONS = (".tar.bz2", ".tbz")
XZ_EXTENSIONS = (".tar.xz", ".txz", ".tlz", ".tar.lz", ".tar.lzma")
ZIP_EXTENSIONS = (".zip", ".whl")
TAR_EXTENSIONS = (".tar.gz", ".tgz", ".tar")
ARCHIVE_EXTENSIONS = ZIP_EXTENSIONS + BZ2_EXTENSIONS + TAR_EXTENSIONS + XZ_EXTENSIONS
SUPPORTED_EXTENSIONS: tuple[str, ...] = ZIP_EXTENSIONS + TAR_EXTENSIONS

try:
    import bz2  # noqa: F401, TC002

    SUPPORTED_EXTENSIONS += BZ2_EXTENSIONS
except ImportError:
    pass

try:
    # Only for Python 3.3+
    import lzma  # noqa: F401, TC002

    SUPPORTED_EXTENSIONS += XZ_EXTENSIONS
except ImportError:
    pass


def path_to_url(path: str | Path) -> str:
    """
    Convert a path to a file: URL.  The path will be made absolute unless otherwise
    specified and have quoted path parts.
    """
    return Path(path).absolute().as_uri()


def url_to_path(url: str) -> Path:
    """
    Convert an RFC8089 file URI to path.

    The logic used here is borrowed from pip
    https://github.com/pypa/pip/blob/4d1932fcdd1974c820ea60b3286984ebb0c3beaa/src/pip/_internal/utils/urls.py#L31
    """
    if not url.startswith("file:"):
        raise ValueError(f"{url} is not a valid file URI")

    _, netloc, path, _, _ = urlsplit(url)

    if not netloc or netloc == "localhost":
        # According to RFC 8089, same as empty authority.
        netloc = ""
    elif netloc not in {".", ".."} and sys.platform == "win32":
        # If we have a UNC path, prepend UNC share notation.
        netloc = "\\\\" + netloc
    else:
        raise ValueError(
            f"non-local file URIs are not supported on this platform: {url}"
        )

    return Path(url2pathname(netloc + unquote(path)))


def is_url(name: str) -> bool:
    if ":" not in name:
        return False
    scheme = name.split(":", 1)[0].lower()

    return scheme in [
        "http",
        "https",
        "file",
        "ftp",
        "ssh",
        "git",
        "hg",
        "bzr",
        "sftp",
        "svn",
        "ssh",
    ]


def strip_extras(path: str) -> tuple[str, str | None]:
    m = re.match(r"^(.+)(\[[^\]]+\])$", path)
    extras = None
    if m:
        path_no_extras = m.group(1)
        extras = m.group(2)
    else:
        path_no_extras = path

    return path_no_extras, extras


def is_installable_dir(path: str) -> bool:
    """Return True if `path` is a directory containing a setup.py file."""
    if not os.path.isdir(path):
        return False
    setup_py = os.path.join(path, "setup.py")
    if os.path.isfile(setup_py):
        return True
    return False


def is_archive_file(name: str) -> bool:
    """Return True if `name` is a considered as an archive file."""
    ext = splitext(name)[1].lower()
    if ext in ARCHIVE_EXTENSIONS:
        return True
    return False


def splitext(path: str) -> tuple[str, str]:
    """Like os.path.splitext, but take off .tar too"""
    base, ext = posixpath.splitext(path)
    if base.lower().endswith(".tar"):
        ext = base[-4:] + ext
        base = base[:-4]
    return base, ext


def convert_markers(marker: BaseMarker) -> ConvertedMarkers:
    from poetry.core.version.markers import MarkerUnion
    from poetry.core.version.markers import MultiMarker
    from poetry.core.version.markers import SingleMarker

    requirements: ConvertedMarkers = {}
    marker = dnf(marker)
    conjunctions = marker.markers if isinstance(marker, MarkerUnion) else [marker]
    group_count = len(conjunctions)

    def add_constraint(
        marker_name: str, constraint: tuple[str, str], group_index: int
    ) -> None:
        # python_full_version is equivalent to python_version
        # for Poetry so we merge them
        if marker_name == "python_full_version":
            marker_name = "python_version"
        if marker_name not in requirements:
            requirements[marker_name] = [[] for _ in range(group_count)]
        requirements[marker_name][group_index].append(constraint)

    for i, sub_marker in enumerate(conjunctions):
        if isinstance(sub_marker, MultiMarker):
            for m in sub_marker.markers:
                if isinstance(m, SingleMarker):
                    add_constraint(m.name, (m.operator, m.value), i)
        elif isinstance(sub_marker, SingleMarker):
            add_constraint(sub_marker.name, (sub_marker.operator, sub_marker.value), i)

    for group_name in requirements:
        # remove duplicates
        seen = []
        for r in requirements[group_name]:
            if r not in seen:
                seen.append(r)
        requirements[group_name] = seen

    return requirements


def contains_group_without_marker(markers: ConvertedMarkers, marker_name: str) -> bool:
    return marker_name not in markers or [] in markers[marker_name]


def create_nested_marker(
    name: str,
    constraint: BaseConstraint | VersionUnion | Version | VersionConstraint,
) -> str:
    from poetry.core.packages.constraints.constraint import Constraint
    from poetry.core.packages.constraints.multi_constraint import MultiConstraint
    from poetry.core.packages.constraints.union_constraint import UnionConstraint
    from poetry.core.semver.version import Version
    from poetry.core.semver.version_union import VersionUnion

    if constraint.is_any():
        return ""

    if isinstance(constraint, (MultiConstraint, UnionConstraint)):
        multi_parts = []
        for c in constraint.constraints:
            multi = isinstance(c, (MultiConstraint, UnionConstraint))
            multi_parts.append((multi, create_nested_marker(name, c)))

        glue = " and "
        if isinstance(constraint, UnionConstraint):
            parts = [f"({part[1]})" if part[0] else part[1] for part in multi_parts]
            glue = " or "
        else:
            parts = [part[1] for part in multi_parts]

        marker = glue.join(parts)
    elif isinstance(constraint, Constraint):
        marker = f'{name} {constraint.operator} "{constraint.version}"'
    elif isinstance(constraint, VersionUnion):
        parts = [create_nested_marker(name, c) for c in constraint.ranges]
        glue = " or "
        parts = [f"({part})" for part in parts]
        marker = glue.join(parts)
    elif isinstance(constraint, Version):
        if name == "python_version" and constraint.precision >= 3:
            name = "python_full_version"

        marker = f'{name} == "{constraint.text}"'
    else:
        assert isinstance(constraint, VersionRange)
        if constraint.min is not None:
            op = ">="
            if not constraint.include_min:
                op = ">"

            version = constraint.min
            if constraint.max is not None:
                min_name = max_name = name
                if min_name == "python_version" and constraint.min.precision >= 3:
                    min_name = "python_full_version"

                if max_name == "python_version" and constraint.max.precision >= 3:
                    max_name = "python_full_version"

                text = f'{min_name} {op} "{version}"'

                op = "<="
                if not constraint.include_max:
                    op = "<"

                version = constraint.max

                text += f' and {max_name} {op} "{version}"'

                return text
        elif constraint.max is not None:
            op = "<="
            if not constraint.include_max:
                op = "<"

            version = constraint.max
        else:
            return ""

        if name == "python_version" and version.precision >= 3:
            name = "python_full_version"

        marker = f'{name} {op} "{version}"'

    return marker


def get_python_constraint_from_marker(
    marker: BaseMarker,
) -> VersionConstraint:
    from poetry.core.semver.empty_constraint import EmptyConstraint
    from poetry.core.semver.helpers import parse_constraint
    from poetry.core.semver.version import Version
    from poetry.core.semver.version_range import VersionRange

    python_marker = marker.only("python_version", "python_full_version")
    if python_marker.is_any():
        return VersionRange()

    if python_marker.is_empty():
        return EmptyConstraint()

    markers = convert_markers(marker)
    if contains_group_without_marker(markers, "python_version"):
        # groups are in disjunctive normal form (DNF),
        # an empty group means that python_version does not appear in this group,
        # which means that python_version is arbitrary for this group
        return VersionRange()

    ors = []
    for or_ in markers["python_version"]:
        ands = []
        for op, version in or_:
            # Expand python version
            if op == "==":
                if "*" not in version:
                    version = "~" + version
                    op = ""
            elif op == "!=":
                if "*" not in version:
                    version += ".*"
            elif op in ("<=", ">"):
                parsed_version = Version.parse(version)
                if parsed_version.precision == 1:
                    if op == "<=":
                        op = "<"
                        version = parsed_version.next_major().text
                    elif op == ">":
                        op = ">="
                        version = parsed_version.next_major().text
                elif parsed_version.precision == 2:
                    if op == "<=":
                        op = "<"
                        version = parsed_version.next_minor().text
                    elif op == ">":
                        op = ">="
                        version = parsed_version.next_minor().text
            elif op in ("in", "not in"):
                versions = []
                for v in re.split("[ ,]+", version):
                    split = v.split(".")
                    if len(split) in [1, 2]:
                        split.append("*")
                        op_ = "" if op == "in" else "!="
                    else:
                        op_ = "==" if op == "in" else "!="

                    versions.append(op_ + ".".join(split))

                glue = " || " if op == "in" else ", "
                if versions:
                    ands.append(glue.join(versions))

                continue

            ands.append(f"{op}{version}")

        ors.append(" ".join(ands))

    return parse_constraint(" || ".join(ors))
