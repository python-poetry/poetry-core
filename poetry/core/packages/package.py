# -*- coding: utf-8 -*-
import copy
import logging
import re

from contextlib import contextmanager
from typing import Union
from warnings import warn

from poetry.core.semver import Version
from poetry.core.semver import parse_constraint
from poetry.core.spdx import License
from poetry.core.spdx import license_by_id
from poetry.core.utils._compat import Path
from poetry.core.utils.helpers import canonicalize_name
from poetry.core.version.markers import AnyMarker
from poetry.core.version.markers import parse_marker

from .constraints import parse_constraint as parse_generic_constraint
from .dependency import Dependency
from .directory_dependency import DirectoryDependency
from .file_dependency import FileDependency
from .url_dependency import URLDependency
from .utils.utils import create_nested_marker
from .vcs_dependency import VCSDependency


AUTHOR_REGEX = re.compile(r"(?u)^(?P<name>[- .,\w\d'’\"()]+)(?: <(?P<email>.+?)>)?$")

logger = logging.getLogger(__name__)


class Package(object):

    AVAILABLE_PYTHONS = {
        "2",
        "2.7",
        "3",
        "3.4",
        "3.5",
        "3.6",
        "3.7",
        "3.8",
        "3.9",
    }

    def __init__(self, name, version, pretty_version=None):
        """
        Creates a new in memory package.
        """
        self._pretty_name = name
        self._name = canonicalize_name(name)

        if not isinstance(version, Version):
            self._version = Version.parse(version)
            self._pretty_version = pretty_version or version
        else:
            self._version = version
            self._pretty_version = pretty_version or self._version.text

        self.description = ""

        self._authors = []
        self._maintainers = []

        self.homepage = None
        self.repository_url = None
        self.documentation_url = None
        self.keywords = []
        self._license = None
        self.readme = None

        self.source_name = ""
        self.source_type = ""
        self.source_reference = ""
        self.source_url = ""

        self.requires = []
        self.dev_requires = []
        self.extras = {}
        self.requires_extras = []

        self.category = "main"
        self.files = []
        self.optional = False

        self.classifiers = []

        self._python_versions = "*"
        self._python_constraint = parse_constraint("*")
        self._python_marker = AnyMarker()

        self.platform = None
        self.marker = AnyMarker()

        self.root_dir = None

        self.develop = True

    @property
    def name(self):
        return self._name

    @property
    def pretty_name(self):
        return self._pretty_name

    @property
    def version(self):
        return self._version

    @property
    def pretty_version(self):
        return self._pretty_version

    @property
    def unique_name(self):
        if self.is_root():
            return self._name

        return self.name + "-" + self._version.text

    @property
    def pretty_string(self):
        return self.pretty_name + " " + self.pretty_version

    @property
    def full_pretty_version(self):
        if self.source_type in ["file", "directory", "url"]:
            return "{} {}".format(self._pretty_version, self.source_url)

        if self.source_type not in ["hg", "git"]:
            return self._pretty_version

        # if source reference is a sha1 hash -- truncate
        if len(self.source_reference) == 40:
            return "{} {}".format(self._pretty_version, self.source_reference[0:7])

        return "{} {}".format(self._pretty_version, self.source_reference)

    @property
    def authors(self):  # type: () -> list
        return self._authors

    @property
    def author_name(self):  # type: () -> str
        return self._get_author()["name"]

    @property
    def author_email(self):  # type: () -> str
        return self._get_author()["email"]

    @property
    def maintainers(self):  # type: () -> list
        return self._maintainers

    @property
    def maintainer_name(self):  # type: () -> str
        return self._get_maintainer()["name"]

    @property
    def maintainer_email(self):  # type: () -> str
        return self._get_maintainer()["email"]

    @property
    def all_requires(self):
        return self.requires + self.dev_requires

    def _get_author(self):  # type: () -> dict
        if not self._authors:
            return {"name": None, "email": None}

        m = AUTHOR_REGEX.match(self._authors[0])

        if m is None:
            raise ValueError(
                "Invalid author string. Must be in the format: "
                "John Smith <john@example.com>"
            )

        name = m.group("name")
        email = m.group("email")

        return {"name": name, "email": email}

    def _get_maintainer(self):  # type: () -> dict
        if not self._maintainers:
            return {"name": None, "email": None}

        m = AUTHOR_REGEX.match(self._maintainers[0])

        if m is None:
            raise ValueError(
                "Invalid maintainer string. Must be in the format: "
                "John Smith <john@example.com>"
            )

        name = m.group("name")
        email = m.group("email")

        return {"name": name, "email": email}

    @property
    def python_versions(self):
        return self._python_versions

    @python_versions.setter
    def python_versions(self, value):
        self._python_versions = value
        self._python_constraint = parse_constraint(value)
        self._python_marker = parse_marker(
            create_nested_marker("python_version", self._python_constraint)
        )

    @property
    def python_constraint(self):
        return self._python_constraint

    @property
    def python_marker(self):
        return self._python_marker

    @property
    def license(self):
        return self._license

    @license.setter
    def license(self, value):
        if value is None:
            self._license = value
        elif isinstance(value, License):
            self._license = value
        else:
            self._license = license_by_id(value)

    @property
    def all_classifiers(self):
        classifiers = copy.copy(self.classifiers)

        # Automatically set python classifiers
        if self.python_versions == "*":
            python_constraint = parse_constraint("~2.7 || ^3.4")
        else:
            python_constraint = self.python_constraint

        for version in sorted(self.AVAILABLE_PYTHONS):
            if len(version) == 1:
                constraint = parse_constraint(version + ".*")
            else:
                constraint = Version.parse(version)

            if python_constraint.allows_any(constraint):
                classifiers.append(
                    "Programming Language :: Python :: {}".format(version)
                )

        # Automatically set license classifiers
        if self.license:
            classifiers.append(self.license.classifier)

        classifiers = set(classifiers)

        return sorted(classifiers)

    @property
    def urls(self):
        urls = {}

        if self.homepage:
            urls["Homepage"] = self.homepage

        if self.repository_url:
            urls["Repository"] = self.repository_url

        if self.documentation_url:
            urls["Documentation"] = self.documentation_url

        return urls

    def is_prerelease(self):
        return self._version.is_prerelease()

    def is_root(self):
        return False

    def add_dependency(
        self,
        name,  # type: str
        constraint=None,  # type: Union[str, dict, None]
        category="main",  # type: str
    ):  # type: (...) -> Dependency
        if constraint is None:
            constraint = "*"

        if isinstance(constraint, dict):
            optional = constraint.get("optional", False)
            python_versions = constraint.get("python")
            platform = constraint.get("platform")
            markers = constraint.get("markers")
            if "allows-prereleases" in constraint:
                message = (
                    'The "{}" dependency specifies '
                    'the "allows-prereleases" property, which is deprecated. '
                    'Use "allow-prereleases" instead.'.format(name)
                )
                warn(message, DeprecationWarning)
                logger.warning(message)

            allows_prereleases = constraint.get(
                "allow-prereleases", constraint.get("allows-prereleases", False)
            )

            if "git" in constraint:
                # VCS dependency
                dependency = VCSDependency(
                    name,
                    "git",
                    constraint["git"],
                    branch=constraint.get("branch", None),
                    tag=constraint.get("tag", None),
                    rev=constraint.get("rev", None),
                    category=category,
                    optional=optional,
                    develop=constraint.get("develop", True),
                )
            elif "file" in constraint:
                file_path = Path(constraint["file"])

                dependency = FileDependency(
                    name, file_path, category=category, base=self.root_dir
                )
            elif "path" in constraint:
                path = Path(constraint["path"])

                if self.root_dir:
                    is_file = (self.root_dir / path).is_file()
                else:
                    is_file = path.is_file()

                if is_file:
                    dependency = FileDependency(
                        name,
                        path,
                        category=category,
                        optional=optional,
                        base=self.root_dir,
                    )
                else:
                    dependency = DirectoryDependency(
                        name,
                        path,
                        category=category,
                        optional=optional,
                        base=self.root_dir,
                        develop=constraint.get("develop", True),
                    )
            elif "url" in constraint:
                dependency = URLDependency(
                    name, constraint["url"], category=category, optional=optional
                )
            else:
                version = constraint["version"]

                dependency = Dependency(
                    name,
                    version,
                    optional=optional,
                    category=category,
                    allows_prereleases=allows_prereleases,
                    source_name=constraint.get("source"),
                )

            if not markers:
                marker = AnyMarker()
                if python_versions:
                    dependency.python_versions = python_versions
                    marker = marker.intersect(
                        parse_marker(
                            create_nested_marker(
                                "python_version", dependency.python_constraint
                            )
                        )
                    )

                if platform:
                    marker = marker.intersect(
                        parse_marker(
                            create_nested_marker(
                                "sys_platform", parse_generic_constraint(platform)
                            )
                        )
                    )
            else:
                marker = parse_marker(markers)

            if not marker.is_any():
                dependency.marker = marker

            if "extras" in constraint:
                for extra in constraint["extras"]:
                    dependency.extras.append(extra)
        else:
            dependency = Dependency(name, constraint, category=category)

        if category == "dev":
            self.dev_requires.append(dependency)
        else:
            self.requires.append(dependency)

        return dependency

    def to_dependency(self):
        from . import dependency_from_pep_508

        name = "{} (=={})".format(self._name, self._version)

        if not self.marker.is_any():
            name += " ; {}".format(str(self.marker))

        return dependency_from_pep_508(name)

    @contextmanager
    def with_python_versions(self, python_versions):
        original_python_versions = self.python_versions

        self.python_versions = python_versions

        yield

        self.python_versions = original_python_versions

    def clone(self):  # type: () -> Package
        clone = self.__class__(self.pretty_name, self.version)
        clone.description = self.description
        clone.category = self.category
        clone.optional = self.optional
        clone.python_versions = self.python_versions
        clone.marker = self.marker
        clone.extras = self.extras
        clone.source_type = self.source_type
        clone.source_url = self.source_url
        clone.source_reference = self.source_reference

        for dep in self.requires:
            clone.requires.append(dep)

        for dep in self.dev_requires:
            clone.dev_requires.append(dep)

        return clone

    def __hash__(self):
        return hash((self._name, self._version))

    def __eq__(self, other):
        if not isinstance(other, Package):
            return NotImplemented

        if self.source_type in ["file", "directory", "url", "git"]:
            if self.source_type != other.source_type:
                return False

            if self.source_url or other.source_url:
                if self.source_url != other.source_url:
                    return False

            if self.source_reference or other.source_reference:
                # special handling for packages with references
                if not self.source_reference or not other.source_reference:
                    # case: one reference is defined and is non-empty, but other is not
                    return False

                if not (
                    self.source_reference == other.source_reference
                    or self.source_reference.startswith(other.source_reference)
                    or other.source_reference.startswith(self.source_reference)
                ):
                    # case: both references defined, but one is not equal to or a short
                    # representation of the other
                    return False

        return self._name == other.name and self._version == other.version

    def __str__(self):
        return self.unique_name

    def __repr__(self):
        return "<Package {} {}>".format(self.name, self.full_pretty_version)
