import copy
import re

from contextlib import contextmanager
from typing import TYPE_CHECKING
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from poetry.core.semver.helpers import parse_constraint
from poetry.core.version.markers import parse_marker

from .specification import PackageSpecification
from .utils.utils import create_nested_marker


if TYPE_CHECKING:
    from poetry.core.semver.helpers import VersionTypes  # noqa
    from poetry.core.semver.version import Version  # noqa
    from poetry.core.spdx.license import License  # noqa
    from poetry.core.version.markers import BaseMarker  # noqa

    from .dependency_group import DependencyGroup
    from .types import DependencyTypes

AUTHOR_REGEX = re.compile(r"(?u)^(?P<name>[- .,\w\d'’\"()&]+)(?: <(?P<email>.+?)>)?$")


class Package(PackageSpecification):

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
        "3.10",
    }

    def __init__(
        self,
        name: str,
        version: Union[str, "Version"],
        pretty_version: Optional[str] = None,
        source_type: Optional[str] = None,
        source_url: Optional[str] = None,
        source_reference: Optional[str] = None,
        source_resolved_reference: Optional[str] = None,
        features: Optional[List[str]] = None,
        develop: bool = False,
    ) -> None:
        """
        Creates a new in memory package.
        """
        from poetry.core.semver.version import Version
        from poetry.core.version.markers import AnyMarker

        super(Package, self).__init__(
            name,
            source_type=source_type,
            source_url=source_url,
            source_reference=source_reference,
            source_resolved_reference=source_resolved_reference,
            features=features,
        )

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

        self.extras = {}
        self.requires_extras = []

        self._dependency_groups: Dict[str, "DependencyGroup"] = {}

        # For compatibility with previous version, we keep the category
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

        self.develop = develop

    @property
    def name(self) -> str:
        return self._name

    @property
    def pretty_name(self) -> str:
        return self._pretty_name

    @property
    def version(self) -> "Version":
        return self._version

    @property
    def pretty_version(self) -> str:
        return self._pretty_version

    @property
    def unique_name(self) -> str:
        if self.is_root():
            return self._name

        return self.complete_name + "-" + self._version.text

    @property
    def pretty_string(self) -> str:
        return self.pretty_name + " " + self.pretty_version

    @property
    def full_pretty_version(self) -> str:
        if self.source_type in ["file", "directory", "url"]:
            return "{} {}".format(self._pretty_version, self.source_url)

        if self.source_type not in ["hg", "git"]:
            return self._pretty_version

        if self.source_resolved_reference:
            if len(self.source_resolved_reference) == 40:
                return "{} {}".format(
                    self._pretty_version, self.source_resolved_reference[0:7]
                )

        # if source reference is a sha1 hash -- truncate
        if len(self.source_reference) == 40:
            return "{} {}".format(self._pretty_version, self.source_reference[0:7])

        return "{} {}".format(
            self._pretty_version,
            self._source_resolved_reference or self._source_reference,
        )

    @property
    def authors(self) -> List[str]:
        return self._authors

    @property
    def author_name(self) -> str:
        return self._get_author()["name"]

    @property
    def author_email(self) -> str:
        return self._get_author()["email"]

    @property
    def maintainers(self) -> List[str]:
        return self._maintainers

    @property
    def maintainer_name(self) -> str:
        return self._get_maintainer()["name"]

    @property
    def maintainer_email(self) -> str:
        return self._get_maintainer()["email"]

    @property
    def requires(self) -> List["DependencyTypes"]:
        """
        Returns the default dependencies
        """
        if not self._dependency_groups or "default" not in self._dependency_groups:
            return []

        return self._dependency_groups["default"].dependencies

    @property
    def all_requires(
        self,
    ) -> List[Union["DependencyTypes"]]:
        """
        Returns the default dependencies and group dependencies.
        """
        return self.requires + [
            dependency
            for group in self._dependency_groups.values()
            for dependency in group.dependencies
            if group.name != "default"
        ]

    def _get_author(self) -> Dict[str, Optional[str]]:
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

    def _get_maintainer(self) -> Dict[str, Optional[str]]:
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
    def python_versions(self) -> str:
        return self._python_versions

    @python_versions.setter
    def python_versions(self, value: str) -> None:
        self._python_versions = value
        self._python_constraint = parse_constraint(value)
        self._python_marker = parse_marker(
            create_nested_marker("python_version", self._python_constraint)
        )

    @property
    def python_constraint(self) -> "VersionTypes":
        return self._python_constraint

    @property
    def python_marker(self) -> "BaseMarker":
        return self._python_marker

    @property
    def license(self) -> "License":
        return self._license

    @license.setter
    def license(self, value: Optional[Union[str, "License"]]) -> None:
        from poetry.core.spdx.helpers import license_by_id
        from poetry.core.spdx.license import License  # noqa

        if value is None:
            self._license = value
        elif isinstance(value, License):
            self._license = value
        else:
            self._license = license_by_id(value)

    @property
    def all_classifiers(self) -> List[str]:
        from poetry.core.semver.version import Version  # noqa

        classifiers = copy.copy(self.classifiers)

        # Automatically set python classifiers
        if self.python_versions == "*":
            python_constraint = parse_constraint("~2.7 || ^3.4")
        else:
            python_constraint = self.python_constraint

        python_classifier_prefix = "Programming Language :: Python"
        python_classifiers = []

        # we sort python versions by sorting an int tuple of (major, minor) version
        # to ensure we sort 3.10 after 3.9
        for version in sorted(
            self.AVAILABLE_PYTHONS, key=lambda x: tuple(map(int, x.split(".")))
        ):
            if len(version) == 1:
                constraint = parse_constraint(version + ".*")
            else:
                constraint = Version.parse(version)

            if python_constraint.allows_any(constraint):
                classifier = "{} :: {}".format(python_classifier_prefix, version)
                if classifier not in python_classifiers:
                    python_classifiers.append(classifier)

        # Automatically set license classifiers
        if self.license:
            classifiers.append(self.license.classifier)

        # Sort classifiers and insert python classifiers at the right location. We do
        # it like this so that 3.10 is sorted after 3.9.
        sorted_classifiers = []
        python_classifiers_inserted = False
        for classifier in sorted(set(classifiers)):
            if (
                not python_classifiers_inserted
                and classifier > python_classifier_prefix
            ):
                sorted_classifiers.extend(python_classifiers)
                python_classifiers_inserted = True
            sorted_classifiers.append(classifier)

        if not python_classifiers_inserted:
            sorted_classifiers.extend(python_classifiers)

        return sorted_classifiers

    @property
    def urls(self) -> Dict[str, str]:
        urls = {}

        if self.homepage:
            urls["Homepage"] = self.homepage

        if self.repository_url:
            urls["Repository"] = self.repository_url

        if self.documentation_url:
            urls["Documentation"] = self.documentation_url

        return urls

    def is_prerelease(self) -> bool:
        return self._version.is_unstable()

    def is_root(self) -> bool:
        return False

    def add_dependency_group(self, group: "DependencyGroup") -> None:
        self._dependency_groups[group.name] = group

    def dependency_group(self, name: str) -> "DependencyGroup":
        if name not in self._dependency_groups:
            raise ValueError(f'The dependency group "{name}" does not exist.')

        return self._dependency_groups[name]

    def add_dependency(
        self,
        dependency: "DependencyTypes",
    ) -> "DependencyTypes":
        from .dependency_group import DependencyGroup

        for group_name in dependency.groups:
            if group_name not in self._dependency_groups:
                # Dynamically add the dependency group
                self.add_dependency_group(DependencyGroup(group_name))

            self._dependency_groups[group_name].add_dependency(dependency)

        return dependency

    def without_dependency_groups(self, groups: List[str]) -> "Package":
        """
        Returns a clone of the package with the given dependency groups excluded.
        """
        package = self.clone()

        for group_name in groups:
            if group_name in package._dependency_groups:
                del package._dependency_groups[group_name]

        return package

    def without_optional_dependency_groups(self) -> "Package":
        """
        Returns a clone of the package without optional dependency groups.
        """
        package = self.clone()

        for group_name, group in self._dependency_groups.items():
            if group.is_optional():
                del package._dependency_groups[group_name]

        return package

    def with_dependency_groups(
        self, groups: List[str], only: bool = False
    ) -> "Package":
        """
        Returns a clone of the package with the given dependency groups opted in.

        Note that it will return all dependencies across all groups
        more the given, optional, groups.

        If `only` is set to True, then only the given groups will be selected.
        """
        package = self.clone()

        for group_name, group in self._dependency_groups.items():
            if only:
                if group_name not in groups:
                    del package._dependency_groups[group_name]
            else:
                if group.is_optional() and group_name not in groups:
                    del package._dependency_groups[group_name]

        return package

    def to_dependency(
        self,
    ) -> Union["DependencyTypes"]:
        from pathlib import Path

        from .dependency import Dependency
        from .directory_dependency import DirectoryDependency
        from .file_dependency import FileDependency
        from .url_dependency import URLDependency
        from .vcs_dependency import VCSDependency

        if self.source_type == "directory":
            dep = DirectoryDependency(
                self._name,
                Path(self._source_url),
                groups=list(self._dependency_groups.keys()),
                optional=self.optional,
                base=self.root_dir,
                develop=self.develop,
                extras=self.features,
            )
        elif self.source_type == "file":
            dep = FileDependency(
                self._name,
                Path(self._source_url),
                groups=list(self._dependency_groups.keys()),
                optional=self.optional,
                base=self.root_dir,
                extras=self.features,
            )
        elif self.source_type == "url":
            dep = URLDependency(
                self._name,
                self._source_url,
                groups=list(self._dependency_groups.keys()),
                optional=self.optional,
                extras=self.features,
            )
        elif self.source_type == "git":
            dep = VCSDependency(
                self._name,
                self.source_type,
                self.source_url,
                rev=self.source_reference,
                resolved_rev=self.source_resolved_reference,
                groups=list(self._dependency_groups.keys()),
                optional=self.optional,
                develop=self.develop,
                extras=self.features,
            )
        else:
            dep = Dependency(self._name, self._version, extras=self.features)

        if not self.marker.is_any():
            dep.marker = self.marker

        if not self.python_constraint.is_any():
            dep.python_versions = self.python_versions

        if self._source_type not in ["directory", "file", "url", "git"]:
            return dep

        return dep.with_constraint(self._version)

    @contextmanager
    def with_python_versions(self, python_versions: str) -> None:
        original_python_versions = self.python_versions

        self.python_versions = python_versions

        yield

        self.python_versions = original_python_versions

    def with_features(self, features: List[str]) -> "Package":
        package = self.clone()

        package._features = frozenset(features)

        return package

    def without_features(self) -> "Package":
        return self.with_features([])

    def clone(self) -> "Package":
        clone = self.__class__(self.pretty_name, self.version)
        clone.__dict__ = copy.deepcopy(self.__dict__)
        return clone

    def __hash__(self) -> int:
        return super(Package, self).__hash__() ^ hash(self._version)

    def __eq__(self, other: "Package") -> bool:
        if not isinstance(other, Package):
            return NotImplemented

        return self.is_same_package_as(other) and self._version == other.version

    def __str__(self) -> str:
        return "{} ({})".format(self.complete_name, self.full_pretty_version)

    def __repr__(self) -> str:
        args = [repr(self._name), repr(self._version.text)]

        if self._features:
            args.append("features={}".format(repr(self._features)))

        if self._source_type:
            args.append("source_type={}".format(repr(self._source_type)))
            args.append("source_url={}".format(repr(self._source_url)))

            if self._source_reference:
                args.append("source_reference={}".format(repr(self._source_reference)))

            if self._source_resolved_reference:
                args.append(
                    "source_resolved_reference={}".format(
                        repr(self._source_resolved_reference)
                    )
                )

        return "Package({})".format(", ".join(args))
