from __future__ import annotations

import copy
import re

from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Collection
from typing import Iterable
from typing import Iterator
from typing import TypeVar
from typing import cast

from poetry.core.packages.dependency_group import MAIN_GROUP
from poetry.core.packages.specification import PackageSpecification
from poetry.core.packages.utils.utils import create_nested_marker
from poetry.core.semver.helpers import parse_constraint
from poetry.core.version.markers import parse_marker


if TYPE_CHECKING:
    from poetry.core.packages.dependency import Dependency
    from poetry.core.packages.dependency_group import DependencyGroup
    from poetry.core.semver.version import Version
    from poetry.core.semver.version_constraint import VersionConstraint
    from poetry.core.spdx.license import License
    from poetry.core.version.markers import BaseMarker

AUTHOR_REGEX = re.compile(r"(?u)^(?P<name>[- .,\w\d'’\"()&]+)(?: <(?P<email>.+?)>)?$")

T = TypeVar("T", bound="Package")


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
        version: str | Version,
        pretty_version: str | None = None,
        source_type: str | None = None,
        source_url: str | None = None,
        source_reference: str | None = None,
        source_resolved_reference: str | None = None,
        source_subdirectory: str | None = None,
        features: Iterable[str] | None = None,
        develop: bool = False,
    ) -> None:
        """
        Creates a new in memory package.
        """
        from poetry.core.semver.version import Version
        from poetry.core.version.markers import AnyMarker

        super().__init__(
            name,
            source_type=source_type,
            source_url=source_url,
            source_reference=source_reference,
            source_resolved_reference=source_resolved_reference,
            source_subdirectory=source_subdirectory,
            features=features,
        )

        if not isinstance(version, Version):
            self._version = Version.parse(version)
            self._pretty_version = pretty_version or version
        else:
            self._version = version
            self._pretty_version = pretty_version or self._version.text

        self.description = ""

        self._authors: list[str] = []
        self._maintainers: list[str] = []

        self.homepage: str | None = None
        self.repository_url: str | None = None
        self.documentation_url: str | None = None
        self.keywords: list[str] = []
        self._license: License | None = None
        self.readmes: tuple[Path, ...] = ()

        self.extras: dict[str, list[Dependency]] = {}
        self.requires_extras: list[str] = []

        self._dependency_groups: dict[str, DependencyGroup] = {}

        # For compatibility with previous version, we keep the category
        self.category = "main"
        self.files: list[dict[str, str]] = []
        self.optional = False

        self.classifiers: list[str] = []

        self._python_versions = "*"
        self._python_constraint = parse_constraint("*")
        self._python_marker: BaseMarker = AnyMarker()

        self.platform = None
        self.marker: BaseMarker = AnyMarker()

        self.root_dir: Path | None = None

        self.develop = develop

    @property
    def name(self) -> str:
        return self._name

    @property
    def pretty_name(self) -> str:
        return self._pretty_name

    @property
    def version(self) -> Version:
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
            return f"{self._pretty_version} {self.source_url}"

        if self.source_type not in ["hg", "git"]:
            return self._pretty_version

        ref: str | None
        if self.source_resolved_reference and len(self.source_resolved_reference) == 40:
            ref = self.source_resolved_reference[0:7]
            return f"{self._pretty_version} {ref}"

        # if source reference is a sha1 hash -- truncate
        if self.source_reference and len(self.source_reference) == 40:
            return f"{self._pretty_version} {self.source_reference[0:7]}"

        ref = self._source_resolved_reference or self._source_reference
        return f"{self._pretty_version} {ref}"

    @property
    def authors(self) -> list[str]:
        return self._authors

    @property
    def author_name(self) -> str | None:
        return self._get_author()["name"]

    @property
    def author_email(self) -> str | None:
        return self._get_author()["email"]

    @property
    def maintainers(self) -> list[str]:
        return self._maintainers

    @property
    def maintainer_name(self) -> str | None:
        return self._get_maintainer()["name"]

    @property
    def maintainer_email(self) -> str | None:
        return self._get_maintainer()["email"]

    @property
    def requires(self) -> list[Dependency]:
        """
        Returns the main dependencies
        """
        if not self._dependency_groups or MAIN_GROUP not in self._dependency_groups:
            return []

        return self._dependency_groups[MAIN_GROUP].dependencies

    @property
    def all_requires(
        self,
    ) -> list[Dependency]:
        """
        Returns the main dependencies and group dependencies.
        """
        return [
            dependency
            for group in self._dependency_groups.values()
            for dependency in group.dependencies
        ]

    def _get_author(self) -> dict[str, str | None]:
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

    def _get_maintainer(self) -> dict[str, str | None]:
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
    def python_constraint(self) -> VersionConstraint:
        return self._python_constraint

    @property
    def python_marker(self) -> BaseMarker:
        return self._python_marker

    @property
    def license(self) -> License | None:
        return self._license

    @license.setter
    def license(self, value: str | License | None) -> None:
        from poetry.core.spdx.helpers import license_by_id
        from poetry.core.spdx.license import License

        if value is None or isinstance(value, License):
            self._license = value
        else:
            self._license = license_by_id(value)

    @property
    def all_classifiers(self) -> list[str]:
        from poetry.core.semver.version import Version

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
                classifier = f"{python_classifier_prefix} :: {version}"
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
    def urls(self) -> dict[str, str]:
        urls = {}

        if self.homepage:
            urls["Homepage"] = self.homepage

        if self.repository_url:
            urls["Repository"] = self.repository_url

        if self.documentation_url:
            urls["Documentation"] = self.documentation_url

        return urls

    @property
    def readme(self) -> Path | None:
        import warnings

        warnings.warn(
            "`readme` is deprecated: you are getting only the first readme file. Please"
            " use the plural form `readmes`.",
            DeprecationWarning,
        )
        return next(iter(self.readmes), None)

    @readme.setter
    def readme(self, path: Path) -> None:
        import warnings

        warnings.warn(
            "`readme` is deprecated. Please assign a tuple to the plural form"
            " `readmes`.",
            DeprecationWarning,
        )
        self.readmes = (path,)

    def is_prerelease(self) -> bool:
        return self._version.is_unstable()

    def is_root(self) -> bool:
        return False

    def dependency_group_names(self, include_optional: bool = False) -> set[str]:
        return {
            name
            for name, group in self._dependency_groups.items()
            if not group.is_optional() or include_optional
        }

    def add_dependency_group(self, group: DependencyGroup) -> None:
        self._dependency_groups[group.name] = group

    def has_dependency_group(self, name: str) -> bool:
        return name in self._dependency_groups

    def dependency_group(self, name: str) -> DependencyGroup:
        if not self.has_dependency_group(name):
            raise ValueError(f'The dependency group "{name}" does not exist.')

        return self._dependency_groups[name]

    def add_dependency(
        self,
        dependency: Dependency,
    ) -> Dependency:
        from poetry.core.packages.dependency_group import DependencyGroup

        for group_name in dependency.groups:
            if group_name not in self._dependency_groups:
                # Dynamically add the dependency group
                self.add_dependency_group(DependencyGroup(group_name))

            self._dependency_groups[group_name].add_dependency(dependency)

        return dependency

    def without_dependency_groups(self: T, groups: Collection[str]) -> T:
        """
        Returns a clone of the package with the given dependency groups excluded.
        """
        package = self.clone()

        for group_name in groups:
            if group_name in package._dependency_groups:
                del package._dependency_groups[group_name]

        return package

    def without_optional_dependency_groups(self: T) -> T:
        """
        Returns a clone of the package without optional dependency groups.
        """
        package = self.clone()

        for group_name, group in self._dependency_groups.items():
            if group.is_optional():
                del package._dependency_groups[group_name]

        return package

    def with_dependency_groups(
        self: T, groups: Collection[str], only: bool = False
    ) -> T:
        """
        Returns a clone of the package with the given dependency groups opted in.

        Note that it will return all dependencies across all groups
        more the given, optional, groups.

        If `only` is set to True, then only the given groups will be selected.
        """
        package = self.clone()

        for group_name, group in self._dependency_groups.items():
            if (only or group.is_optional()) and group_name not in groups:
                del package._dependency_groups[group_name]

        return package

    def to_dependency(self) -> Dependency:
        from pathlib import Path

        from poetry.core.packages.dependency import Dependency
        from poetry.core.packages.directory_dependency import DirectoryDependency
        from poetry.core.packages.file_dependency import FileDependency
        from poetry.core.packages.url_dependency import URLDependency
        from poetry.core.packages.vcs_dependency import VCSDependency

        dep: Dependency
        if self.source_type == "directory":
            dep = DirectoryDependency(
                self._name,
                Path(cast(str, self._source_url)),
                groups=list(self._dependency_groups.keys()),
                optional=self.optional,
                base=self.root_dir,
                develop=self.develop,
                extras=self.features,
            )
        elif self.source_type == "file":
            dep = FileDependency(
                self._name,
                Path(cast(str, self._source_url)),
                groups=list(self._dependency_groups.keys()),
                optional=self.optional,
                base=self.root_dir,
                extras=self.features,
            )
        elif self.source_type == "url":
            dep = URLDependency(
                self._name,
                cast(str, self._source_url),
                groups=list(self._dependency_groups.keys()),
                optional=self.optional,
                extras=self.features,
            )
        elif self.source_type == "git":
            dep = VCSDependency(
                self._name,
                self.source_type,
                cast(str, self.source_url),
                rev=self.source_reference,
                resolved_rev=self.source_resolved_reference,
                directory=self.source_subdirectory,
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

        if not self.is_direct_origin():
            return dep

        return dep.with_constraint(self._version)

    @contextmanager
    def with_python_versions(self, python_versions: str) -> Iterator[None]:
        original_python_versions = self.python_versions

        self.python_versions = python_versions

        yield

        self.python_versions = original_python_versions

    def with_features(self: T, features: Iterable[str]) -> T:
        package = self.clone()

        package._features = frozenset(features)

        return package

    def without_features(self: T) -> T:
        return self.with_features([])

    def satisfies(
        self, dependency: Dependency, ignore_source_type: bool = False
    ) -> bool:
        """
        Helper method to check if this package satisfies a given dependency.

        This is determined by assessing if this instance provides the package and
        features specified by the given dependency. Further, version and source
        types are checked.
        """
        if not self.provides(dependency) or not dependency.constraint.allows(
            self.version
        ):
            return False

        return ignore_source_type or self.is_same_source_as(dependency)

    def clone(self: T) -> T:
        clone = self.__class__(self.pretty_name, self.version)
        clone.__dict__ = copy.deepcopy(self.__dict__)
        return clone

    def __hash__(self) -> int:
        return super().__hash__() ^ hash(self._version)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Package):
            return NotImplemented

        return self.is_same_package_as(other) and self._version == other.version

    def __str__(self) -> str:
        return f"{self.complete_name} ({self.full_pretty_version})"

    def __repr__(self) -> str:
        args = [repr(self._name), repr(self._version.text)]

        if self._features:
            args.append(f"features={repr(self._features)}")

        if self._source_type:
            args.append(f"source_type={repr(self._source_type)}")
            args.append(f"source_url={repr(self._source_url)}")

            if self._source_reference:
                args.append(f"source_reference={repr(self._source_reference)}")

            if self._source_resolved_reference:
                args.append(
                    f"source_resolved_reference={repr(self._source_resolved_reference)}"
                )
            if self._source_subdirectory:
                args.append(f"source_subdirectory={repr(self._source_subdirectory)}")

        args_str = ", ".join(args)
        return f"Package({args_str})"
