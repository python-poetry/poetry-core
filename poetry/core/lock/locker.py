import itertools
import json
import logging
import re

from copy import deepcopy
from hashlib import sha256
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from tomlkit import document
from tomlkit import inline_table
from tomlkit import item
from tomlkit import table
from tomlkit.container import Container as TOMLContainer
from tomlkit.exceptions import TOMLKitError

from poetry.core.lock.categories import LockCategory
from poetry.core.packages.package import Dependency
from poetry.core.packages.package import Package
from poetry.core.pyproject import PyProjectTOML
from poetry.core.semver import parse_constraint
from poetry.core.semver.version import Version
from poetry.core.toml import TOMLFile
from poetry.core.utils._compat import Path  # noqa
from poetry.core.version.markers import parse_marker


logger = logging.getLogger(__name__)


Data = Union[Dict[str, Any], TOMLContainer]


class Locker(object):

    _VERSION = "1.1"

    _relevant_keys = ["dependencies", "dev-dependencies", "source", "extras"]

    def __init__(self, lock, local_config=None):  # type: (Path, Optional[Data]) -> None
        self._lock = TOMLFile(lock)
        self._local_config = local_config
        self._lock_data = None
        self._content_hash = self._get_content_hash()

    @property
    def lock(self):  # type: () -> TOMLFile
        return self._lock

    @property
    def lock_data(self):
        if self._lock_data is None:
            self._lock_data = self._get_lock_data()

        return self._lock_data

    def is_locked(self):  # type: () -> bool
        """
        Checks whether the locker has been locked (lockfile found).
        """
        if not self._lock.exists():
            return False

        return "package" in self.lock_data

    def is_fresh(self):  # type: () -> bool
        """
        Checks whether the lock file is still up to date with the current hash.
        """
        lock = self._lock.read()
        metadata = lock.get("metadata", {})

        if "content-hash" in metadata:
            return self._content_hash == lock["metadata"]["content-hash"]

        return False

    def get_packages(
        self, names=None, categories=None
    ):  # type: (Optional[List[str]], Optional[List[LockCategory]]) -> List[Package]
        """
        Get locked packages. Filters by categories if specified.

        :param names: Package names to filter on.
        :param categories: Package categories to filter on.
        """
        packages = []

        if not self.is_locked():
            return packages

        locked_packages = [
            pkg
            for pkg in self.lock_data["package"]
            if (names is None or pkg["name"] in names)
            and (categories is None or pkg["category"] in categories)
        ]
        lock_metadata = self.lock_data["metadata"]

        for info in locked_packages:
            packages.append(self._load_package(info, lock_metadata))

        return packages

    def get_project_dependencies(
        self, project_requires, pinned_versions=False, with_nested=False
    ):  # type: (List[Dependency], bool, bool) -> Any
        packages = self.get_packages(categories=[LockCategory.MAIN])

        # group packages entries by name, this is required because requirement might use
        # different constraints
        packages_by_name = {}
        for pkg in packages:
            if pkg.name not in packages_by_name:
                packages_by_name[pkg.name] = []
            packages_by_name[pkg.name].append(pkg)

        def __get_locked_package(
            _dependency,
        ):  # type: (Dependency) -> Optional[Package]
            """
            Internal helper to identify corresponding locked package using dependency
            version constraints.
            """
            for _package in packages_by_name.get(_dependency.name, []):
                if _dependency.constraint.allows(_package.version):
                    return _package
            return None

        project_level_dependencies = set()
        dependencies = []

        for dependency in project_requires:
            dependency = deepcopy(dependency)
            if pinned_versions:
                locked_package = __get_locked_package(dependency)
                if locked_package:
                    dependency.constraint = locked_package.to_dependency().constraint
            project_level_dependencies.add(dependency.name)
            dependencies.append(dependency)

        if not with_nested:
            # return only with project level dependencies
            return dependencies

        nested_dependencies = []

        for pkg in packages:  # type: Package
            for requirement in pkg.requires:  # type: Dependency
                if requirement.name in project_level_dependencies:
                    # project level dependencies take precedence
                    continue

                if pinned_versions:
                    requirement.constraint = (
                        __get_locked_package(requirement).to_dependency().constraint
                    )

                # dependencies use extra to indicate that it was activated via parent
                # package's extras
                marker = requirement.marker.without_extras()
                for project_requirement in project_requires:
                    if (
                        pkg.name == project_requirement.name
                        and project_requirement.constraint.allows(pkg.version)
                    ):
                        requirement.marker = marker.intersect(
                            project_requirement.marker
                        )
                        break
                else:
                    # this dependency was not from a project requirement
                    requirement.marker = marker.intersect(pkg.marker)

                if requirement not in nested_dependencies:
                    nested_dependencies.append(requirement)

        return sorted(
            itertools.chain(dependencies, nested_dependencies),
            key=lambda x: x.name.lower(),
        )

    def set_lock_data(self, root, packages):  # type: (...) -> bool
        files = table()
        packages = self._lock_packages(packages)
        # Retrieving hashes
        for package in packages:
            if package["name"] not in files:
                files[package["name"]] = []

            for f in package["files"]:
                file_metadata = inline_table()
                for k, v in sorted(f.items()):
                    file_metadata[k] = v

                files[package["name"]].append(file_metadata)  # noqa

            if files[package["name"]]:
                files[package["name"]] = item(files[package["name"]]).multiline(True)

            del package["files"]

        lock = document()
        lock["package"] = packages

        if root.extras:
            lock["extras"] = {
                extra: [dep.pretty_name for dep in deps]
                for extra, deps in root.extras.items()
            }

        lock["metadata"] = {
            "lock-version": self._VERSION,
            "python-versions": root.python_versions,
            "content-hash": self._content_hash,
            "files": files,
        }

        if not self.is_locked() or lock != self.lock_data:
            self._write_lock_data(lock)

            return True

        return False

    def _write_lock_data(self, data):
        self.lock.write(data)

        # Checking lock file data consistency
        if data != self.lock.read():
            raise RuntimeError("Inconsistent lock file data.")

        self._lock_data = None

    def _get_content_hash(self):  # type: () -> str
        """
        Returns the sha256 hash of the sorted content of the pyproject file.
        """
        if self._local_config is None:
            return ""

        content = self._local_config

        relevant_content = {}
        for key in self._relevant_keys:
            relevant_content[key] = content.get(key)

        content_hash = sha256(
            json.dumps(relevant_content, sort_keys=True).encode()
        ).hexdigest()

        return content_hash

    def _get_lock_data(self):  # type: () -> dict
        if not self._lock.exists():
            raise RuntimeError("No lockfile found. Unable to read locked packages")

        try:
            lock_data = self._lock.read()
        except TOMLKitError as e:
            raise RuntimeError("Unable to read the lock file ({}).".format(e))

        lock_version = Version.parse(lock_data["metadata"].get("lock-version", "1.0"))
        current_version = Version.parse(self._VERSION)
        # We expect the locker to be able to read lock files
        # from the same semantic versioning range
        accepted_versions = parse_constraint(
            "^{}".format(Version(current_version.major, 0))
        )
        lock_version_allowed = accepted_versions.allows(lock_version)
        if lock_version_allowed and current_version < lock_version:
            logger.warning(
                "The lock file might not be compatible with the current version of Poetry.\n"
                "Upgrade Poetry to ensure the lock file is read properly or, alternatively, "
                "regenerate the lock file with the `poetry lock` command."
            )
        elif not lock_version_allowed:
            raise RuntimeError(
                "The lock file is not compatible with the current version of Poetry.\n"
                "Upgrade Poetry to be able to read the lock file or, alternatively, "
                "regenerate the lock file with the `poetry lock` command."
            )

        return lock_data

    def _lock_packages(self, packages):  # type: (List[Package]) -> list
        locked = []

        for package in sorted(packages, key=lambda x: x.name):
            spec = self._dump_package(package)

            locked.append(spec)

        return locked

    @staticmethod
    def _load_package(info, lock_metadata):  # type: (Data, Data) -> Package
        package = Package(
            name=info["name"], version=info["version"], pretty_version=info["version"]
        )
        package.description = info.get("description", "")
        package.category = info["category"]
        package.optional = info["optional"]
        if lock_metadata and "hashes" in lock_metadata:
            # Old lock so we create dummy files from the hashes
            package.files = [
                {"name": h, "hash": h} for h in lock_metadata["hashes"][info["name"]]
            ]
        else:
            package.files = lock_metadata["files"][info["name"]]

        package.python_versions = info["python-versions"]
        extras = info.get("extras", {})
        if extras:
            for name, deps in extras.items():
                package.extras[name] = []

                for dep in deps:
                    m = re.match(r"^(.+?)(?:\s+\((.+)\))?$", dep)
                    dep_name = m.group(1)
                    constraint = m.group(2) or "*"

                    package.extras[name].append(Dependency(dep_name, constraint))

        if "marker" in info:
            package.marker = parse_marker(info["marker"])
        else:
            # Compatibility for old locks
            if "requirements" in info:
                dep = Dependency("foo", "0.0.0")
                for name, value in info["requirements"].items():
                    if name == "python":
                        dep.python_versions = value
                    elif name == "platform":
                        dep.platform = value

                split_dep = dep.to_pep_508(False).split(";")
                if len(split_dep) > 1:
                    package.marker = parse_marker(split_dep[1].strip())

        for dep_name, constraint in info.get("dependencies", {}).items():
            if isinstance(constraint, list):
                for c in constraint:
                    package.add_dependency(dep_name, c)

                continue

            package.add_dependency(dep_name, constraint)

        if "develop" in info:
            package.develop = info["develop"]

        if "source" in info:
            package.source_type = info["source"].get("type", "")
            package.source_url = info["source"]["url"]
            package.source_reference = info["source"]["reference"]

        return package

    @staticmethod
    def _dump_package(package):  # type: (Package) -> dict
        dependencies = {}
        for dependency in sorted(package.requires, key=lambda d: d.name):
            if dependency.is_optional() and not dependency.is_activated():
                continue

            if dependency.pretty_name not in dependencies:
                dependencies[dependency.pretty_name] = []

            constraint = inline_table()
            constraint["version"] = str(dependency.pretty_constraint)

            if dependency.extras:
                constraint["extras"] = sorted(dependency.extras)

            if dependency.is_optional():
                constraint["optional"] = True

            if not dependency.marker.is_any():
                constraint["markers"] = str(dependency.marker)

            dependencies[dependency.pretty_name].append(constraint)

        # All the constraints should have the same type,
        # but we want to simplify them if it's possible
        for dependency, constraints in tuple(dependencies.items()):
            if all(len(constraint) == 1 for constraint in constraints):
                dependencies[dependency] = [
                    constraint["version"] for constraint in constraints
                ]

        data = {
            "name": package.pretty_name,
            "version": package.pretty_version,
            "description": package.description or "",
            "category": package.category,
            "optional": package.optional,
            "python-versions": package.python_versions,
            "files": sorted(package.files, key=lambda x: x["file"]),
        }

        if package.extras:
            extras = {}
            for name, deps in package.extras.items():
                extras[name] = [
                    str(dep) if not dep.constraint.is_any() else dep.name
                    for dep in deps
                ]

            data["extras"] = extras

        if dependencies:
            for k, constraints in dependencies.items():
                if len(constraints) == 1:
                    dependencies[k] = constraints[0]

            data["dependencies"] = dependencies

        if package.source_url:
            data["source"] = {
                "url": package.source_url,
                "reference": package.source_reference,
            }
            if package.source_type:
                data["source"]["type"] = package.source_type
            if package.source_type == "directory":
                data["develop"] = package.develop

        return data

    @classmethod
    def load(cls, lock, pyproject_file=None):  # type: (Path, Optional[Path]) -> Locker
        if pyproject_file and pyproject_file.exists():
            return cls(lock, PyProjectTOML(pyproject_file).poetry_config)
        return cls(lock)
