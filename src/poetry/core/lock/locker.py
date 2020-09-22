import json
import logging
import os
import re

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

from tomlkit import array
from tomlkit import document
from tomlkit import inline_table
from tomlkit import item
from tomlkit import table
from tomlkit.exceptions import TOMLKitError

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.package import Package
from poetry.core.pyproject.toml import PyProjectTOML
from poetry.core.semver.helpers import parse_constraint
from poetry.core.semver.version import Version
from poetry.core.toml.file import TOMLFile
from poetry.core.version.markers import parse_marker
from poetry.core.version.requirements import InvalidRequirement


if TYPE_CHECKING:
    from tomlkit.container import Container as TOMLContainer
    from tomlkit.items import InlineTable
    from tomlkit.toml_document import TOMLDocument

    Data = Union[Dict[str, Any], TOMLContainer]

logger = logging.getLogger(__name__)


class Locker:

    _VERSION = "1.1"

    _relevant_keys = ["dependencies", "group", "source", "extras"]

    def __init__(
        self, lock: Union[str, Path], local_config: Optional["Data"] = None
    ) -> None:
        self._lock = TOMLFile(lock)
        self._local_config = local_config or {}
        self._lock_data = None
        self._content_hash = self._get_content_hash()

    @property
    def lock(self) -> TOMLFile:
        return self._lock

    @property
    def lock_data(self) -> "TOMLDocument":
        if self._lock_data is None:
            self._lock_data = self._get_lock_data()

        return self._lock_data

    def is_locked(self) -> bool:
        """
        Checks whether the locker has been locked (lockfile found).
        """
        if not self._lock.exists():
            return False

        return "package" in self.lock_data

    def is_fresh(self) -> bool:
        """
        Checks whether the lock file is still up to date with the current hash.
        """
        lock = self._lock.read()
        metadata = lock.get("metadata", {})

        if "content-hash" in metadata:
            return self._content_hash == lock["metadata"]["content-hash"]  # type: ignore[no-any-return]

        return False

    @staticmethod
    def __get_locked_package(
        _dependency: Dependency, packages_by_name: Dict[str, List[Package]]
    ) -> Union[Package, None]:
        """
        Internal helper to identify corresponding locked package using dependency
        version constraints.
        """
        for _package in packages_by_name.get(_dependency.name, []):
            if _dependency.constraint.allows(_package.version):
                return _package
        return None

    @classmethod
    def __walk_dependency_level(
        cls,
        dependencies: List[Dependency],
        level: int,
        pinned_versions: bool,
        packages_by_name: Dict[str, List[Package]],
        project_level_dependencies: Set[str],
        nested_dependencies: Dict[Tuple[str, str], Dependency],
    ) -> Dict[Tuple[str, str], Dependency]:
        if not dependencies:
            return nested_dependencies

        next_level_dependencies = []

        for requirement in dependencies:
            key = (requirement.name, requirement.pretty_constraint)
            locked_package = cls.__get_locked_package(requirement, packages_by_name)

            if locked_package:
                # create dependency from locked package to retain dependency metadata
                # if this is not done, we can end-up with incorrect nested dependencies
                constraint = requirement.constraint
                pretty_constraint = requirement.pretty_constraint
                marker = requirement.marker
                requirement = locked_package.to_dependency()
                requirement.marker = requirement.marker.intersect(marker)

                key = (requirement.name, pretty_constraint)

                if not pinned_versions:
                    requirement.set_constraint(constraint)

                for require in locked_package.requires:
                    if require.marker.is_empty():
                        require.marker = requirement.marker
                    else:
                        require.marker = require.marker.intersect(requirement.marker)

                    require.marker = require.marker.intersect(locked_package.marker)

                    if key not in nested_dependencies:
                        next_level_dependencies.append(require)

            if requirement.name in project_level_dependencies and level == 0:
                # project level dependencies take precedence
                continue

            if not locked_package:
                # we make a copy to avoid any side-effects
                requirement = deepcopy(requirement)

            if key not in nested_dependencies:
                nested_dependencies[key] = requirement
            else:
                nested_dependencies[key].marker = nested_dependencies[key].marker.union(
                    requirement.marker
                )

        return cls.__walk_dependency_level(
            dependencies=next_level_dependencies,
            level=level + 1,
            pinned_versions=pinned_versions,
            packages_by_name=packages_by_name,
            project_level_dependencies=project_level_dependencies,
            nested_dependencies=nested_dependencies,
        )

    @classmethod
    def get_project_dependencies(
        cls,
        project_requires: List[Dependency],
        locked_packages: List[Package],
        pinned_versions: bool = False,
        with_nested: bool = False,
    ) -> Iterable[Dependency]:
        # group packages entries by name, this is required because requirement might use
        # different constraints
        packages_by_name: Dict[str, List[Package]] = {}
        for pkg in locked_packages:
            if pkg.name not in packages_by_name:
                packages_by_name[pkg.name] = []
            packages_by_name[pkg.name].append(pkg)

        project_level_dependencies = set()
        dependencies = []

        for dependency in project_requires:
            dependency = deepcopy(dependency)
            locked_package = cls.__get_locked_package(dependency, packages_by_name)
            if locked_package:
                locked_dependency = locked_package.to_dependency()
                locked_dependency.marker = dependency.marker.intersect(
                    locked_package.marker
                )

                if not pinned_versions:
                    locked_dependency.set_constraint(dependency.constraint)

                dependency = locked_dependency

            project_level_dependencies.add(dependency.name)
            dependencies.append(dependency)

        if not with_nested:
            # return only with project level dependencies
            return dependencies

        nested_dependencies = cls.__walk_dependency_level(
            dependencies=dependencies,
            level=0,
            pinned_versions=pinned_versions,
            packages_by_name=packages_by_name,
            project_level_dependencies=project_level_dependencies,
            nested_dependencies={},
        )

        # Merge same dependencies using marker union
        for requirement in dependencies:
            key = (requirement.name, requirement.pretty_constraint)
            if key not in nested_dependencies:
                nested_dependencies[key] = requirement
            else:
                nested_dependencies[key].marker = nested_dependencies[key].marker.union(
                    requirement.marker
                )

        return sorted(nested_dependencies.values(), key=lambda x: x.name.lower())

    def _load_package(self, info: "Data") -> Package:
        from poetry.core.factory import Factory

        lock_metadata = self.lock_data["metadata"]
        source = info.get("source", {})
        source_type = source.get("type")
        url = source.get("url")
        if source_type in ["directory", "file"]:
            url = self._lock.path.parent.joinpath(url).resolve().as_posix()

        package = Package(
            info["name"],
            info["version"],
            info["version"],
            source_type=source_type,
            source_url=url,
            source_reference=source.get("reference"),
            source_resolved_reference=source.get("resolved_reference"),
        )
        package.description = info.get("description", "")
        package.category = info.get("category", "main")
        # package.groups = info.get("groups", ["default"])  # noqa: E800
        package.optional = info["optional"]
        if "hashes" in lock_metadata:
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
                    try:
                        dependency = Dependency.create_from_pep_508(dep)
                    except InvalidRequirement:
                        # handle lock files with invalid PEP 508
                        m = re.match(r"^(.+?)(?:\[(.+?)])?(?:\s+\((.+)\))?$", dep)
                        if not m:
                            raise
                        dep_name = m.group(1)
                        extras = m.group(2) or ""
                        constraint = m.group(3) or "*"
                        dependency = Dependency(
                            dep_name, constraint, extras=extras.split(",")
                        )
                    package.extras[name].append(dependency)

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

            root_dir = self._lock.path.parent
            if package.source_type == "directory" and package.source_url is not None:
                # root dir should be the source of the package relative to the lock
                # path
                root_dir = Path(package.source_url)

            if isinstance(constraint, list):
                for c in constraint:
                    package.add_dependency(
                        Factory.create_dependency(dep_name, c, root_dir=root_dir)
                    )

                continue

            package.add_dependency(
                Factory.create_dependency(dep_name, constraint, root_dir=root_dir)
            )

        if "develop" in info:
            package.develop = info["develop"]

        return package

    @classmethod
    def load(
        cls, lock: Path, pyproject_file: Optional[Union[str, Path]] = None
    ) -> "Locker":
        if pyproject_file and Path(pyproject_file).exists():
            return cls(lock, PyProjectTOML(pyproject_file).poetry_config)
        return cls(lock)

    def get_packages(
        self, names: Optional[List[str]] = None, categories: Optional[List[str]] = None
    ) -> List[Package]:
        """
        Get locked packages. Filters by categories if specified.
        :param names: Package names to filter on.
        :param categories: Package categories to filter on.
        """
        packages: List[Package] = []

        if not self.is_locked():
            return packages

        locked_packages = [
            pkg
            for pkg in self.lock_data["package"]
            if (names is None or pkg["name"] in names)
            and (categories is None or pkg["category"] in categories)
        ]

        for info in locked_packages:
            packages.append(self._load_package(info))

        return packages

    def set_lock_data(self, root: Package, packages: List[Package]) -> bool:
        files = table()
        _packages = self._lock_packages(packages)
        # Retrieving hashes
        for package in _packages:
            if package["name"] not in files:
                files[package["name"]] = []

            for f in package["files"]:
                file_metadata = inline_table()
                for k, v in sorted(f.items()):
                    file_metadata[k] = v

                files[package["name"]].append(file_metadata)

            if files[package["name"]]:
                files[package["name"]] = item(files[package["name"]]).multiline(True)

            del package["files"]

        lock = document()
        lock["package"] = _packages

        if root.extras:
            lock["extras"] = {
                extra: [dep.pretty_name for dep in deps]
                for extra, deps in sorted(root.extras.items())
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

    def _write_lock_data(self, data: "TOMLDocument") -> None:
        self.lock.write(data)

        # Checking lock file data consistency
        if data != self.lock.read():
            raise RuntimeError("Inconsistent lock file data.")

        self._lock_data = None

    def _get_content_hash(self) -> str:
        """
        Returns the sha256 hash of the sorted content of the pyproject file.
        """
        content = self._local_config

        relevant_content = {}
        for key in self._relevant_keys:
            relevant_content[key] = content.get(key)

        content_hash = sha256(
            json.dumps(relevant_content, sort_keys=True).encode()
        ).hexdigest()

        return content_hash

    def _get_lock_data(self) -> "TOMLDocument":
        if not self._lock.exists():
            raise RuntimeError("No lockfile found. Unable to read locked packages")

        try:
            lock_data = self._lock.read()
        except TOMLKitError as e:
            raise RuntimeError(f"Unable to read the lock file ({e}).")

        lock_version = Version.parse(lock_data["metadata"].get("lock-version", "1.0"))
        current_version = Version.parse(self._VERSION)
        # We expect the locker to be able to read lock files
        # from the same semantic versioning range
        accepted_versions = parse_constraint(
            f"^{Version.from_parts(current_version.major, 0)}"
        )
        lock_version_allowed = accepted_versions.allows(lock_version)
        if lock_version_allowed and current_version < lock_version:
            logger.warning(
                "The lock file might not be compatible with the current version of"
                " Poetry.\nUpgrade Poetry to ensure the lock file is read properly or,"
                " alternatively, regenerate the lock file with the `poetry lock`"
                " command."
            )
        elif not lock_version_allowed:
            raise RuntimeError(
                "The lock file is not compatible with the current version of Poetry.\n"
                "Upgrade Poetry to be able to read the lock file or, alternatively, "
                "regenerate the lock file with the `poetry lock` command."
            )

        return lock_data

    def _lock_packages(self, packages: List[Package]) -> List[Dict[str, Any]]:
        locked: List[Data] = []

        for package in sorted(packages, key=lambda x: x.name):
            spec = self._dump_package(package)

            locked.append(spec)

        return locked

    def _dump_package(self, package: Package) -> "Data":
        dependencies: Dict[str, List["InlineTable"]] = {}
        for require in sorted(package.requires, key=lambda d: d.name):
            if require.pretty_name not in dependencies:
                dependencies[require.pretty_name] = []

            constraint = inline_table()

            if require.is_directory() or require.is_file():
                constraint["path"] = require.path.as_posix()  # type: ignore[attr-defined]

                if require.is_directory() and require.develop:  # type: ignore[attr-defined]
                    constraint["develop"] = True
            elif require.is_url():
                constraint["url"] = require.url  # type: ignore[attr-defined]
            elif require.is_vcs():
                constraint[require.vcs] = require.source  # type: ignore[attr-defined]

                if require.branch:  # type: ignore[attr-defined]
                    constraint["branch"] = require.branch  # type: ignore[attr-defined]
                elif require.tag:  # type: ignore[attr-defined]
                    constraint["tag"] = require.tag  # type: ignore[attr-defined]
                elif require.rev:  # type: ignore[attr-defined]
                    constraint["rev"] = require.rev  # type: ignore[attr-defined]
            else:
                constraint["version"] = str(require.pretty_constraint)

            if require.extras:
                constraint["extras"] = sorted(require.extras)

            if require.is_optional():
                constraint["optional"] = True

            if not require.marker.is_any():
                constraint["markers"] = str(require.marker)

            dependencies[require.pretty_name].append(constraint)

        # All the constraints should have the same type,
        # but we want to simplify them if it's possible
        for dependency, constraints in tuple(dependencies.items()):
            if all(
                len(constraint) == 1 and "version" in constraint
                for constraint in constraints
            ):
                dependencies[dependency] = [
                    constraint["version"] for constraint in constraints
                ]

        data: "Data" = {
            "name": package.pretty_name,
            "version": package.pretty_version,
            "description": package.description or "",
            "category": package.category,
            "optional": package.optional,
            "python-versions": package.python_versions,
            "files": sorted(package.files, key=lambda x: x["file"]),  # type: ignore[no-any-return]
        }

        if dependencies:
            data["dependencies"] = table()
            for k, constraints in dependencies.items():
                if len(constraints) == 1:
                    data["dependencies"][k] = constraints[0]
                else:
                    data["dependencies"][k] = array().multiline(True)
                    for constraint in constraints:
                        data["dependencies"][k].append(constraint)

        if package.extras:
            extras = {}
            for name, deps in package.extras.items():
                extras[name] = [
                    dep.to_pep_508() if not dep.constraint.is_any() else dep.name
                    for dep in deps
                ]

            data["extras"] = extras

        if package.source_url:
            url = package.source_url
            if package.source_type in ["file", "directory"]:
                # The lock file should only store paths relative to the root project
                url = Path(
                    os.path.relpath(
                        Path(url).as_posix(), self._lock.path.parent.as_posix()
                    )
                ).as_posix()

            data["source"] = {}

            if package.source_type:
                data["source"]["type"] = package.source_type

            data["source"]["url"] = url

            if package.source_reference:
                data["source"]["reference"] = package.source_reference

            if package.source_resolved_reference:
                data["source"]["resolved_reference"] = package.source_resolved_reference

            if package.source_type in ["directory", "git"]:
                data["develop"] = package.develop

        return data
