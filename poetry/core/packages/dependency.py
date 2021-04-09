import os
import re

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import FrozenSet
from typing import List
from typing import Optional
from typing import Union

from poetry.core.semver.helpers import parse_constraint
from poetry.core.version.markers import parse_marker

from .constraints import parse_constraint as parse_generic_constraint
from .specification import PackageSpecification


if TYPE_CHECKING:
    from poetry.core.semver.helpers import VersionTypes  # noqa
    from poetry.core.version.markers import BaseMarker  # noqa

    from .constraints import BaseConstraint  # noqa
    from .directory_dependency import DirectoryDependency  # noqa
    from .file_dependency import FileDependency  # noqa
    from .package import Package
    from .types import DependencyTypes


class Dependency(PackageSpecification):
    def __init__(
        self,
        name: str,
        constraint: Union[str, "VersionTypes"],
        optional: bool = False,
        category: str = "main",
        allows_prereleases: bool = False,
        extras: Union[List[str], FrozenSet[str]] = None,
        source_type: Optional[str] = None,
        source_url: Optional[str] = None,
        source_reference: Optional[str] = None,
        source_resolved_reference: Optional[str] = None,
    ):
        from poetry.core.semver.version_range import VersionRange
        from poetry.core.version.markers import AnyMarker

        super(Dependency, self).__init__(
            name,
            source_type=source_type,
            source_url=source_url,
            source_reference=source_reference,
            source_resolved_reference=source_resolved_reference,
            features=extras,
        )

        self._constraint = None
        self.set_constraint(constraint=constraint)

        self._pretty_constraint = str(constraint)
        self._optional = optional
        self._category = category

        if isinstance(self._constraint, VersionRange) and self._constraint.min:
            allows_prereleases = (
                allows_prereleases or self._constraint.min.is_unstable()
            )

        self._allows_prereleases = allows_prereleases

        self._python_versions = "*"
        self._python_constraint = parse_constraint("*")
        self._transitive_python_versions = None
        self._transitive_python_constraint = None
        self._transitive_marker = None
        self._extras = frozenset(extras or [])

        self._in_extras = []

        self._activated = not self._optional

        self.is_root = False
        self.marker = AnyMarker()
        self.source_name = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def constraint(self) -> "VersionTypes":
        return self._constraint

    def set_constraint(self, constraint: Union[str, "VersionTypes"]) -> None:
        from poetry.core.semver.version_constraint import VersionConstraint

        try:
            if not isinstance(constraint, VersionConstraint):
                self._constraint = parse_constraint(constraint)
            else:
                self._constraint = constraint
        except ValueError:
            self._constraint = parse_constraint("*")

    @property
    def pretty_constraint(self) -> str:
        return self._pretty_constraint

    @property
    def pretty_name(self) -> str:
        return self._pretty_name

    @property
    def category(self) -> str:
        return self._category

    @property
    def python_versions(self) -> str:
        return self._python_versions

    @python_versions.setter
    def python_versions(self, value: str) -> None:
        self._python_versions = value
        self._python_constraint = parse_constraint(value)
        if not self._python_constraint.is_any():
            self.marker = self.marker.intersect(
                parse_marker(
                    self._create_nested_marker(
                        "python_version", self._python_constraint
                    )
                )
            )

    @property
    def transitive_python_versions(self) -> str:
        if self._transitive_python_versions is None:
            return self._python_versions

        return self._transitive_python_versions

    @transitive_python_versions.setter
    def transitive_python_versions(self, value: str) -> None:
        self._transitive_python_versions = value
        self._transitive_python_constraint = parse_constraint(value)

    @property
    def transitive_marker(self) -> "BaseMarker":
        if self._transitive_marker is None:
            return self.marker

        return self._transitive_marker

    @transitive_marker.setter
    def transitive_marker(self, value: "BaseMarker") -> None:
        self._transitive_marker = value

    @property
    def python_constraint(self) -> "VersionTypes":
        return self._python_constraint

    @property
    def transitive_python_constraint(self) -> "VersionTypes":
        if self._transitive_python_constraint is None:
            return self._python_constraint

        return self._transitive_python_constraint

    @property
    def extras(self) -> FrozenSet[str]:
        return self._extras

    @property
    def in_extras(self) -> List[str]:
        return self._in_extras

    @property
    def base_pep_508_name(self) -> str:
        from poetry.core.semver.version import Version
        from poetry.core.semver.version_union import VersionUnion

        requirement = self.pretty_name

        if self.extras:
            requirement += "[{}]".format(",".join(self.extras))

        if isinstance(self.constraint, VersionUnion):
            if self.constraint.excludes_single_version():
                requirement += " ({})".format(str(self.constraint))
            else:
                constraints = self.pretty_constraint.split(",")
                constraints = [parse_constraint(c) for c in constraints]
                constraints = [str(c) for c in constraints]
                requirement += " ({})".format(",".join(constraints))
        elif isinstance(self.constraint, Version):
            requirement += " (=={})".format(self.constraint.text)
        elif not self.constraint.is_any():
            requirement += " ({})".format(str(self.constraint).replace(" ", ""))

        return requirement

    def allows_prereleases(self) -> bool:
        return self._allows_prereleases

    def is_optional(self) -> bool:
        return self._optional

    def is_activated(self) -> bool:
        return self._activated

    def is_vcs(self) -> bool:
        return False

    def is_file(self) -> bool:
        return False

    def is_directory(self) -> bool:
        return False

    def is_url(self) -> bool:
        return False

    def accepts(self, package: "Package") -> bool:
        """
        Determines if the given package matches this dependency.
        """
        return (
            self._name == package.name
            and self._constraint.allows(package.version)
            and (not package.is_prerelease() or self.allows_prereleases())
        )

    def to_pep_508(self, with_extras: bool = True) -> str:
        from .utils.utils import convert_markers

        requirement = self.base_pep_508_name

        markers = []
        has_extras = False
        if not self.marker.is_any():
            marker = self.marker
            if not with_extras:
                marker = marker.without_extras()

            # we re-check for any marker here since the without extra marker might
            # return an any marker again
            if not marker.is_empty() and not marker.is_any():
                markers.append(str(marker))

            has_extras = "extra" in convert_markers(marker)
        else:
            # Python marker
            if self.python_versions != "*":
                python_constraint = self.python_constraint

                markers.append(
                    self._create_nested_marker("python_version", python_constraint)
                )

        in_extras = " || ".join(self._in_extras)
        if in_extras and with_extras and not has_extras:
            markers.append(
                self._create_nested_marker("extra", parse_generic_constraint(in_extras))
            )

        if markers:
            if self.is_vcs() or self.is_url():
                requirement += " "

            if len(markers) > 1:
                markers = ["({})".format(m) for m in markers]
                requirement += "; {}".format(" and ".join(markers))
            else:
                requirement += "; {}".format(markers[0])

        return requirement

    def _create_nested_marker(
        self, name: str, constraint: Union["BaseConstraint", "VersionTypes"]
    ) -> str:
        from poetry.core.semver.version import Version
        from poetry.core.semver.version_union import VersionUnion

        from .constraints.constraint import Constraint
        from .constraints.multi_constraint import MultiConstraint
        from .constraints.union_constraint import UnionConstraint

        if isinstance(constraint, (MultiConstraint, UnionConstraint)):
            parts = []
            for c in constraint.constraints:
                multi = False
                if isinstance(c, (MultiConstraint, UnionConstraint)):
                    multi = True

                parts.append((multi, self._create_nested_marker(name, c)))

            glue = " and "
            if isinstance(constraint, UnionConstraint):
                parts = [
                    "({})".format(part[1]) if part[0] else part[1] for part in parts
                ]
                glue = " or "
            else:
                parts = [part[1] for part in parts]

            marker = glue.join(parts)
        elif isinstance(constraint, Constraint):
            marker = '{} {} "{}"'.format(name, constraint.operator, constraint.version)
        elif isinstance(constraint, VersionUnion):
            parts = []
            for c in constraint.ranges:
                parts.append(self._create_nested_marker(name, c))

            glue = " or "
            parts = ["({})".format(part) for part in parts]

            marker = glue.join(parts)
        elif isinstance(constraint, Version):
            if constraint.precision >= 3 and name == "python_version":
                name = "python_full_version"

            marker = '{} == "{}"'.format(name, constraint.text)
        else:
            if constraint.min is not None:
                min_name = name
                if constraint.min.precision >= 3 and name == "python_version":
                    min_name = "python_full_version"

                    if constraint.max is None:
                        name = min_name

                op = ">="
                if not constraint.include_min:
                    op = ">"

                version = constraint.min.text
                if constraint.max is not None:
                    max_name = name
                    if constraint.max.precision >= 3 and name == "python_version":
                        max_name = "python_full_version"

                    text = '{} {} "{}"'.format(min_name, op, version)

                    op = "<="
                    if not constraint.include_max:
                        op = "<"

                    version = constraint.max

                    text += ' and {} {} "{}"'.format(max_name, op, version)

                    return text
            elif constraint.max is not None:
                if constraint.max.precision >= 3 and name == "python_version":
                    name = "python_full_version"

                op = "<="
                if not constraint.include_max:
                    op = "<"

                version = constraint.max
            else:
                return ""

            marker = '{} {} "{}"'.format(name, op, version)

        return marker

    def activate(self) -> None:
        """
        Set the dependency as mandatory.
        """
        self._activated = True

    def deactivate(self) -> None:
        """
        Set the dependency as optional.
        """
        if not self._optional:
            self._optional = True

        self._activated = False

    def with_constraint(self, constraint: Union[str, "VersionTypes"]) -> "Dependency":
        new = Dependency(
            self.pretty_name,
            constraint,
            optional=self.is_optional(),
            category=self.category,
            allows_prereleases=self.allows_prereleases(),
            extras=self._extras,
            source_type=self._source_type,
            source_url=self._source_url,
            source_reference=self._source_reference,
        )

        new.is_root = self.is_root
        new.python_versions = self.python_versions
        new.transitive_python_versions = self.transitive_python_versions
        new.marker = self.marker
        new.transitive_marker = self.transitive_marker

        for in_extra in self.in_extras:
            new.in_extras.append(in_extra)

        return new

    @classmethod
    def create_from_pep_508(
        cls, name: str, relative_to: Optional[Path] = None
    ) -> "DependencyTypes":
        """
        Resolve a PEP-508 requirement string to a `Dependency` instance. If a `relative_to`
        path is specified, this is used as the base directory if the identified dependency is
        of file or directory type.
        """
        from poetry.core.utils.patterns import wheel_file_re
        from poetry.core.vcs.git import ParsedUrl
        from poetry.core.version.requirements import Requirement

        from .url_dependency import URLDependency
        from .utils.link import Link
        from .utils.utils import convert_markers
        from .utils.utils import is_archive_file
        from .utils.utils import is_installable_dir
        from .utils.utils import is_url
        from .utils.utils import path_to_url
        from .utils.utils import strip_extras
        from .utils.utils import url_to_path
        from .vcs_dependency import VCSDependency

        # Removing comments
        parts = name.split("#", 1)
        name = parts[0].strip()
        if len(parts) > 1:
            rest = parts[1]
            if " ;" in rest:
                name += " ;" + rest.split(" ;", 1)[1]

        req = Requirement(name)

        if req.marker:
            markers = convert_markers(req.marker)
        else:
            markers = {}

        name = req.name
        path = os.path.normpath(os.path.abspath(name))
        link = None

        if is_url(name):
            link = Link(name)
        elif req.url:
            link = Link(req.url)
        else:
            p, extras = strip_extras(path)
            if os.path.isdir(p) and (os.path.sep in name or name.startswith(".")):

                if not is_installable_dir(p):
                    raise ValueError(
                        "Directory {!r} is not installable. File 'setup.py' "
                        "not found.".format(name)
                    )
                link = Link(path_to_url(p))
            elif is_archive_file(p):
                link = Link(path_to_url(p))

        # it's a local file, dir, or url
        if link:
            is_file_uri = link.scheme == "file"
            is_relative_uri = is_file_uri and re.search(r"\.\./", link.url)

            # Handle relative file URLs
            if is_file_uri and is_relative_uri:
                path = Path(link.path)
                if relative_to:
                    path = relative_to / path
                link = Link(path_to_url(path))

            # wheel file
            version = None
            if link.is_wheel:
                m = wheel_file_re.match(link.filename)
                if not m:
                    raise ValueError("Invalid wheel name: {}".format(link.filename))
                name = m.group("name")
                version = m.group("ver")

            name = req.name or link.egg_fragment
            dep = None

            if link.scheme.startswith("git+"):
                url = ParsedUrl.parse(link.url)
                dep = VCSDependency(
                    name, "git", url.url, rev=url.rev, extras=req.extras
                )
            elif link.scheme == "git":
                dep = VCSDependency(
                    name, "git", link.url_without_fragment, extras=req.extras
                )
            elif link.scheme in ["http", "https"]:
                dep = URLDependency(name, link.url)
            elif is_file_uri:
                # handle RFC 8089 references
                path = url_to_path(req.url)
                dep = _make_file_or_dir_dep(
                    name=name, path=path, base=relative_to, extras=req.extras
                )
            else:
                try:
                    # this is a local path not using the file URI scheme
                    dep = _make_file_or_dir_dep(
                        name=name,
                        path=Path(req.url),
                        base=relative_to,
                        extras=req.extras,
                    )
                except ValueError:
                    pass

            if dep is None:
                dep = Dependency(name, version or "*", extras=req.extras)

            if version:
                dep._constraint = parse_constraint(version)
        else:
            if req.pretty_constraint:
                constraint = req.constraint
            else:
                constraint = "*"

            dep = Dependency(name, constraint, extras=req.extras)

        if "extra" in markers:
            # If we have extras, the dependency is optional
            dep.deactivate()

            for or_ in markers["extra"]:
                for _, extra in or_:
                    dep.in_extras.append(extra)

        if "python_version" in markers:
            ors = []
            for or_ in markers["python_version"]:
                ands = []
                for op, version in or_:
                    # Expand python version
                    if op == "==" and "*" not in version:
                        version = "~" + version
                        op = ""
                    elif op == "!=":
                        version += ".*"
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

                    ands.append("{}{}".format(op, version))

                ors.append(" ".join(ands))

            dep.python_versions = " || ".join(ors)

        if req.marker:
            dep.marker = req.marker

        return dep

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Dependency):
            return NotImplemented

        return (
            self.is_same_package_as(other)
            and self._constraint == other.constraint
            and self._extras == other.extras
        )

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return (
            super(Dependency, self).__hash__()
            ^ hash(self._constraint)
            ^ hash(self._extras)
        )

    def __str__(self) -> str:
        if self.is_root:
            return self._pretty_name
        return self.base_pep_508_name

    def __repr__(self) -> str:
        return "<{} {}>".format(self.__class__.__name__, str(self))


def _make_file_or_dir_dep(
    name: str,
    path: Path,
    base: Optional[Path] = None,
    extras: Optional[List[str]] = None,
) -> Optional[Union["FileDependency", "DirectoryDependency"]]:
    """
    Helper function to create a file or directoru dependency with the given arguments. If
    path is not a file or directory that exists, `None` is returned.
    """
    from .directory_dependency import DirectoryDependency
    from .file_dependency import FileDependency

    _path = path
    if not path.is_absolute() and base:
        # a base path was specified, so we should respect that
        _path = Path(base) / path

    if _path.is_file():
        return FileDependency(name, path, base=base, extras=extras)
    elif _path.is_dir():
        return DirectoryDependency(name, path, base=base, extras=extras)

    return None
