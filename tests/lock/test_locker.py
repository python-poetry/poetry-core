import logging
import tempfile

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import tomlkit

from poetry.core.factory import Factory
from poetry.core.lock import Locker
from poetry.core.packages.package import Package
from poetry.core.packages.project_package import ProjectPackage
from poetry.core.semver.version import Version


if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture


@pytest.fixture  # type: ignore[misc]
def locker() -> Locker:
    with tempfile.NamedTemporaryFile() as f:
        f.close()
        locker = Locker(Path(f.name), {})

        return locker


@pytest.fixture  # type: ignore[misc]
def root() -> ProjectPackage:
    return ProjectPackage("root", "1.2.3")


def test_lock_file_data_is_ordered(locker: Locker, root: ProjectPackage) -> None:
    package_a = Package("A", "1.0.0")
    package_a.add_dependency(Factory.create_dependency("B", "^1.0"))
    package_a.files = [{"file": "foo", "hash": "456"}, {"file": "bar", "hash": "123"}]
    package_git = Package(
        "git-package",
        "1.2.3",
        source_type="git",
        source_url="https://github.com/python-poetry/poetry.git",
        source_reference="develop",
        source_resolved_reference="123456",
    )
    packages = [package_a, Package("B", "1.2"), package_git]

    locker.set_lock_data(root, packages)

    with locker.lock.open(encoding="utf-8") as f:
        content = f.read()

    expected = """[[package]]
name = "A"
version = "1.0.0"
description = ""
category = "main"
optional = false
python-versions = "*"

[package.dependencies]
B = "^1.0"

[[package]]
name = "B"
version = "1.2"
description = ""
category = "main"
optional = false
python-versions = "*"

[[package]]
name = "git-package"
version = "1.2.3"
description = ""
category = "main"
optional = false
python-versions = "*"
develop = false

[package.source]
type = "git"
url = "https://github.com/python-poetry/poetry.git"
reference = "develop"
resolved_reference = "123456"

[metadata]
lock-version = "1.1"
python-versions = "*"
content-hash = "178f2cd01dc40e96be23a4a0ae1094816626346346618335e5ff4f0b2c0c5831"

[metadata.files]
A = [
    {file = "bar", hash = "123"},
    {file = "foo", hash = "456"},
]
B = []
git-package = []
"""

    assert content == expected


def test_locker_properly_loads_extras(locker: Locker) -> None:
    content = """\
[[package]]
name = "cachecontrol"
version = "0.12.5"
description = "httplib2 caching for requests"
category = "main"
optional = false
python-versions = ">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*"

[package.dependencies]
msgpack = "*"
requests = "*"

[package.dependencies.lockfile]
optional = true
version = ">=0.9"

[package.extras]
filecache = ["lockfile (>=0.9)"]
redis = ["redis (>=2.10.5)"]

[metadata]
lock-version = "1.1"
python-versions = "~2.7 || ^3.4"
content-hash = "c3d07fca33fba542ef2b2a4d75bf5b48d892d21a830e2ad9c952ba5123a52f77"

[metadata.files]
cachecontrol = []
"""

    locker.lock.write(tomlkit.parse(content))

    packages = locker.get_packages()

    assert len(packages) == 1

    package = packages[0]
    assert len(package.requires) == 3
    assert len(package.extras) == 2

    lockfile_dep = package.extras["filecache"][0]
    assert lockfile_dep.name == "lockfile"


def test_locker_properly_loads_nested_extras(locker: Locker) -> None:
    content = """\
[[package]]
name = "a"
version = "1.0"
description = ""
category = "main"
optional = false
python-versions = "*"

[package.dependencies]
b = {version = "^1.0", optional = true, extras = "c"}

[package.extras]
b = ["b[c] (>=1.0,<2.0)"]

[[package]]
name = "b"
version = "1.0"
description = ""
category = "main"
optional = false
python-versions = "*"

[package.dependencies]
c = {version = "^1.0", optional = true}

[package.extras]
c = ["c (>=1.0,<2.0)"]

[[package]]
name = "c"
version = "1.0"
description = ""
category = "main"
optional = false
python-versions = "*"

[metadata]
python-versions = "*"
lock-version = "1.1"
content-hash = "123456789"

[metadata.files]
"a" = []
"b" = []
"c" = []
"""

    locker.lock.write(tomlkit.parse(content))

    packages = locker.get_packages()
    assert len(packages) == 3

    packages = locker.get_packages(["a"])
    assert len(packages) == 1

    package = packages[0]
    assert len(package.requires) == 1
    assert len(package.extras) == 1

    dependency_b = package.extras["b"][0]
    assert dependency_b.name == "b"
    assert dependency_b.extras == frozenset({"c"})

    packages = locker.get_packages([dependency_b.name])
    assert len(packages) == 1

    package = packages[0]
    assert len(package.requires) == 1
    assert len(package.extras) == 1

    dependency_c = package.extras["c"][0]
    assert dependency_c.name == "c"
    assert dependency_c.extras == frozenset()

    packages = locker.get_packages([dependency_c.name])
    assert len(packages) == 1


def test_locker_properly_loads_extras_legacy(locker: Locker) -> None:
    content = """\
[[package]]
name = "a"
version = "1.0"
description = ""
category = "main"
optional = false
python-versions = "*"

[package.dependencies]
b = {version = "^1.0", optional = true}

[package.extras]
b = ["b (^1.0)"]

[[package]]
name = "b"
version = "1.0"
description = ""
category = "main"
optional = false
python-versions = "*"

[metadata]
python-versions = "*"
lock-version = "1.1"
content-hash = "123456789"

[metadata.files]
"a" = []
"b" = []
"""

    locker.lock.write(tomlkit.parse(content))

    packages = locker.get_packages()
    assert len(packages) == 2

    packages = locker.get_packages(["a"])
    assert len(packages) == 1

    package = packages[0]
    assert len(package.requires) == 1
    assert len(package.extras) == 1

    dependency_b = package.extras["b"][0]
    assert dependency_b.name == "b"


def test_lock_packages_with_null_description(
    locker: Locker, root: ProjectPackage
) -> None:
    package_a = Package("A", "1.0.0")
    package_a.description = None  # type: ignore[assignment]

    locker.set_lock_data(root, [package_a])

    with locker.lock.open(encoding="utf-8") as f:
        content = f.read()

    expected = """[[package]]
name = "A"
version = "1.0.0"
description = ""
category = "main"
optional = false
python-versions = "*"

[metadata]
lock-version = "1.1"
python-versions = "*"
content-hash = "178f2cd01dc40e96be23a4a0ae1094816626346346618335e5ff4f0b2c0c5831"

[metadata.files]
A = []
"""

    assert content == expected


def test_lock_file_should_not_have_mixed_types(
    locker: Locker, root: ProjectPackage
) -> None:
    package_a = Package("A", "1.0.0")
    package_a.add_dependency(Factory.create_dependency("B", "^1.0.0"))
    package_a.add_dependency(
        Factory.create_dependency("B", {"version": ">=1.0.0", "optional": True})
    )
    package_a.requires[-1].activate()
    package_a.extras["foo"] = [Factory.create_dependency("B", ">=1.0.0")]

    locker.set_lock_data(root, [package_a])

    expected = """[[package]]
name = "A"
version = "1.0.0"
description = ""
category = "main"
optional = false
python-versions = "*"

[package.dependencies]
B = [
    {version = "^1.0.0"},
    {version = ">=1.0.0", optional = true},
]

[package.extras]
foo = ["B (>=1.0.0)"]

[metadata]
lock-version = "1.1"
python-versions = "*"
content-hash = "178f2cd01dc40e96be23a4a0ae1094816626346346618335e5ff4f0b2c0c5831"

[metadata.files]
A = []
"""

    with locker.lock.open(encoding="utf-8") as f:
        content = f.read()

    assert content == expected


def test_reading_lock_file_should_raise_an_error_on_invalid_data(
    locker: Locker,
) -> None:
    content = """[[package]]
name = "A"
version = "1.0.0"
description = ""
category = "main"
optional = false
python-versions = "*"

[package.extras]
foo = ["bar"]

[package.extras]
foo = ["bar"]

[metadata]
lock-version = "1.1"
python-versions = "*"
content-hash = "178f2cd01dc40e96be23a4a0ae1094816626346346618335e5ff4f0b2c0c5831"

[metadata.files]
A = []
"""
    with locker.lock.open("w", encoding="utf-8") as f:
        f.write(content)

    with pytest.raises(RuntimeError) as e:
        _ = locker.lock_data

    assert "Unable to read the lock file" in str(e.value)


def test_locking_legacy_repository_package_should_include_source_section(
    root: ProjectPackage, locker: Locker
) -> None:
    package_a = Package(
        "A",
        "1.0.0",
        source_type="legacy",
        source_url="https://foo.bar",
        source_reference="legacy",
    )
    packages = [package_a]

    locker.set_lock_data(root, packages)

    with locker.lock.open(encoding="utf-8") as f:
        content = f.read()

    expected = """[[package]]
name = "A"
version = "1.0.0"
description = ""
category = "main"
optional = false
python-versions = "*"

[package.source]
type = "legacy"
url = "https://foo.bar"
reference = "legacy"

[metadata]
lock-version = "1.1"
python-versions = "*"
content-hash = "178f2cd01dc40e96be23a4a0ae1094816626346346618335e5ff4f0b2c0c5831"

[metadata.files]
A = []
"""

    assert content == expected


def test_locker_should_emit_warnings_if_lock_version_is_newer_but_allowed(
    locker: Locker, caplog: "LogCaptureFixture"
) -> None:
    version = ".".join(Version.parse(Locker._VERSION).next_minor().text.split(".")[:2])
    content = f"""\
[metadata]
lock-version = "{version}"
python-versions = "~2.7 || ^3.4"
content-hash = "c3d07fca33fba542ef2b2a4d75bf5b48d892d21a830e2ad9c952ba5123a52f77"

[metadata.files]
"""
    caplog.set_level(logging.WARNING, logger="poetry.packages.locker")

    locker.lock.write(tomlkit.parse(content))

    _ = locker.lock_data

    assert len(caplog.records) == 1

    record = caplog.records[0]
    assert record.levelname == "WARNING"

    expected = """\
The lock file might not be compatible with the current version of Poetry.
Upgrade Poetry to ensure the lock file is read properly or, alternatively, \
regenerate the lock file with the `poetry lock` command.\
"""
    assert record.message == expected


def test_locker_should_raise_an_error_if_lock_version_is_newer_and_not_allowed(
    locker: Locker, caplog: "LogCaptureFixture"
) -> None:
    content = """\
[metadata]
lock-version = "2.0"
python-versions = "~2.7 || ^3.4"
content-hash = "c3d07fca33fba542ef2b2a4d75bf5b48d892d21a830e2ad9c952ba5123a52f77"

[metadata.files]
"""
    caplog.set_level(logging.WARNING, logger="poetry.packages.locker")

    locker.lock.write(tomlkit.parse(content))

    with pytest.raises(RuntimeError, match="^The lock file is not compatible"):
        _ = locker.lock_data


def test_extras_dependencies_are_ordered(locker: Locker, root: ProjectPackage) -> None:
    package_a = Package("A", "1.0.0")
    package_a.add_dependency(
        Factory.create_dependency(
            "B", {"version": "^1.0.0", "optional": True, "extras": ["c", "a", "b"]}
        )
    )
    package_a.requires[-1].activate()

    locker.set_lock_data(root, [package_a])

    expected = """[[package]]
name = "A"
version = "1.0.0"
description = ""
category = "main"
optional = false
python-versions = "*"

[package.dependencies]
B = {version = "^1.0.0", extras = ["a", "b", "c"], optional = true}

[metadata]
lock-version = "1.1"
python-versions = "*"
content-hash = "178f2cd01dc40e96be23a4a0ae1094816626346346618335e5ff4f0b2c0c5831"

[metadata.files]
A = []
"""

    with locker.lock.open(encoding="utf-8") as f:
        content = f.read()

    assert content == expected


def test_locker_should_neither_emit_warnings_nor_raise_error_for_lower_compatible_versions(
    locker: Locker, caplog: "LogCaptureFixture"
) -> None:
    current_version = Version.parse(Locker._VERSION)
    older_version = ".".join(
        [str(current_version.major), str(current_version.minor - 1)]  # type: ignore[operator]
    )
    content = f"""\
[metadata]
lock-version = "{older_version}"
python-versions = "~2.7 || ^3.4"
content-hash = "c3d07fca33fba542ef2b2a4d75bf5b48d892d21a830e2ad9c952ba5123a52f77"

[metadata.files]
"""
    caplog.set_level(logging.WARNING, logger="poetry.packages.locker")

    locker.lock.write(tomlkit.parse(content))

    _ = locker.lock_data

    assert len(caplog.records) == 0


def test_locker_dumps_dependency_information_correctly(
    locker: Locker, root: ProjectPackage
) -> None:
    root_dir = Path(__file__).parent.parent.joinpath("fixtures")
    package_a = Package("A", "1.0.0")
    package_a.add_dependency(
        Factory.create_dependency(
            "B", {"path": "project_with_extras", "develop": True}, root_dir=root_dir
        )
    )
    package_a.add_dependency(
        Factory.create_dependency(
            "C",
            {"path": "project_with_transitive_directory_dependencies"},
            root_dir=root_dir,
        )
    )
    package_a.add_dependency(
        Factory.create_dependency(
            "D", {"path": "distributions/demo-0.1.0.tar.gz"}, root_dir=root_dir
        )
    )
    package_a.add_dependency(
        Factory.create_dependency(
            "E", {"url": "https://python-poetry.org/poetry-1.2.0.tar.gz"}
        )
    )
    package_a.add_dependency(
        Factory.create_dependency(
            "F", {"git": "https://github.com/python-poetry/poetry.git", "branch": "foo"}
        )
    )

    packages = [package_a]

    locker.set_lock_data(root, packages)

    with locker.lock.open(encoding="utf-8") as f:
        content = f.read()

    expected = """[[package]]
name = "A"
version = "1.0.0"
description = ""
category = "main"
optional = false
python-versions = "*"

[package.dependencies]
B = {path = "project_with_extras", develop = true}
C = {path = "project_with_transitive_directory_dependencies"}
D = {path = "distributions/demo-0.1.0.tar.gz"}
E = {url = "https://python-poetry.org/poetry-1.2.0.tar.gz"}
F = {git = "https://github.com/python-poetry/poetry.git", branch = "foo"}

[metadata]
lock-version = "1.1"
python-versions = "*"
content-hash = "178f2cd01dc40e96be23a4a0ae1094816626346346618335e5ff4f0b2c0c5831"

[metadata.files]
A = []
"""

    assert content == expected
