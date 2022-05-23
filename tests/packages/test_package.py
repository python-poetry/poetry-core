from __future__ import annotations

import random

from pathlib import Path
from typing import cast

import pytest

from poetry.core.factory import Factory
from poetry.core.packages.dependency import Dependency
from poetry.core.packages.dependency_group import DependencyGroup
from poetry.core.packages.directory_dependency import DirectoryDependency
from poetry.core.packages.file_dependency import FileDependency
from poetry.core.packages.package import Package
from poetry.core.packages.url_dependency import URLDependency
from poetry.core.packages.vcs_dependency import VCSDependency


@pytest.fixture()
def package_with_groups() -> Package:
    package = Package("foo", "1.2.3")

    optional_group = DependencyGroup("optional", optional=True)
    optional_group.add_dependency(Factory.create_dependency("bam", "^3.0.0"))

    package.add_dependency(Factory.create_dependency("bar", "^1.0.0"))
    package.add_dependency(Factory.create_dependency("baz", "^1.1.0"))
    package.add_dependency(Factory.create_dependency("bim", "^2.0.0", groups=["dev"]))
    package.add_dependency_group(optional_group)

    return package


def test_package_authors() -> None:
    package = Package("foo", "0.1.0")

    package.authors.append("Sébastien Eustace <sebastien@eustace.io>")
    assert package.author_name == "Sébastien Eustace"
    assert package.author_email == "sebastien@eustace.io"

    package.authors.insert(0, "John Doe")
    assert package.author_name == "John Doe"
    assert package.author_email is None


def test_package_authors_invalid() -> None:
    package = Package("foo", "0.1.0")

    package.authors.insert(0, "<John Doe")
    with pytest.raises(ValueError) as e:
        package.author_name

    assert (
        str(e.value)
        == "Invalid author string. Must be in the format: John Smith <john@example.com>"
    )


@pytest.mark.parametrize("groups", [["main"], ["dev"]])
def test_package_add_dependency_vcs_groups(groups: list[str], f: Factory) -> None:
    package = Package("foo", "0.1.0")

    dependency = package.add_dependency(
        f.create_dependency(
            "poetry",
            {"git": "https://github.com/python-poetry/poetry.git"},
            groups=groups,
        )
    )
    assert dependency.groups == frozenset(groups)


def test_package_add_dependency_vcs_groups_default_main(f: Factory) -> None:
    package = Package("foo", "0.1.0")

    dependency = package.add_dependency(
        f.create_dependency(
            "poetry", {"git": "https://github.com/python-poetry/poetry.git"}
        )
    )
    assert dependency.groups == frozenset(["main"])


@pytest.mark.parametrize("groups", [["main"], ["dev"]])
@pytest.mark.parametrize("optional", [True, False])
def test_package_url_groups_optional(
    groups: list[str], optional: bool, f: Factory
) -> None:
    package = Package("foo", "0.1.0")

    dependency = package.add_dependency(
        f.create_dependency(
            "poetry",
            {
                "url": "https://github.com/python-poetry/poetry/releases/download/1.0.5/poetry-1.0.5-linux.tar.gz",
                "optional": optional,
            },
            groups=groups,
        )
    )
    assert dependency.groups == frozenset(groups)
    assert dependency.is_optional() == optional


def test_package_equality_simple() -> None:
    assert Package("foo", "0.1.0") == Package("foo", "0.1.0")
    assert Package("foo", "0.1.0") != Package("foo", "0.1.1")
    assert Package("bar", "0.1.0") != Package("foo", "0.1.0")


def test_package_equality_source_type() -> None:
    a1 = Package("a", "0.1.0", source_type="file")
    a2 = Package(a1.name, a1.version, source_type="directory")
    a3 = Package(a1.name, a1.version, source_type=a1.source_type)
    a4 = Package(a1.name, a1.version)

    assert a1 == a1
    assert a1 == a3
    assert a1 != a2
    assert a2 != a3
    assert a1 != a4
    assert a2 != a4


def test_package_equality_source_url() -> None:
    a1 = Package("a", "0.1.0", source_type="file", source_url="/some/path")
    a2 = Package(
        a1.name, a1.version, source_type=a1.source_type, source_url="/some/other/path"
    )
    a3 = Package(
        a1.name, a1.version, source_type=a1.source_type, source_url=a1.source_url
    )
    a4 = Package(a1.name, a1.version, source_type=a1.source_type)

    assert a1 == a1
    assert a1 == a3
    assert a1 != a2
    assert a2 != a3
    assert a1 != a4
    assert a2 != a4


def test_package_equality_source_reference() -> None:
    a1 = Package(
        "a",
        "0.1.0",
        source_type="git",
        source_url="https://foo.bar",
        source_reference="c01b317af582501c5ba07b23d5bef3fbada2d4ef",
    )
    a2 = Package(
        a1.name,
        a1.version,
        source_type="git",
        source_url="https://foo.bar",
        source_reference="a444731cd243cb5cd04e4d5fb81f86e1fecf8a00",
    )
    a3 = Package(
        a1.name,
        a1.version,
        source_type="git",
        source_url="https://foo.bar",
        source_reference="c01b317af582501c5ba07b23d5bef3fbada2d4ef",
    )
    a4 = Package(a1.name, a1.version, source_type="git")

    assert a1 == a1
    assert a1 == a3
    assert a1 != a2
    assert a2 != a3
    assert a1 != a4
    assert a2 != a4


def test_package_resolved_reference_is_relevant_for_equality_only_if_present_for_both_packages() -> None:
    a1 = Package(
        "a",
        "0.1.0",
        source_type="git",
        source_url="https://foo.bar",
        source_reference="master",
        source_resolved_reference="c01b317af582501c5ba07b23d5bef3fbada2d4ef",
    )
    a2 = Package(
        a1.name,
        a1.version,
        source_type="git",
        source_url="https://foo.bar",
        source_reference="master",
        source_resolved_reference="a444731cd243cb5cd04e4d5fb81f86e1fecf8a00",
    )
    a3 = Package(
        a1.name,
        a1.version,
        source_type="git",
        source_url="https://foo.bar",
        source_reference="master",
        source_resolved_reference="c01b317af582501c5ba07b23d5bef3fbada2d4ef",
    )
    a4 = Package(
        a1.name,
        a1.version,
        source_type="git",
        source_url="https://foo.bar",
        source_reference="master",
    )

    assert a1 == a1
    assert a1 == a3
    assert a1 != a2
    assert a2 != a3
    assert a1 == a4
    assert a2 == a4


def test_package_equality_source_subdirectory() -> None:
    a1 = Package(
        "a",
        "0.1.0",
        source_type="git",
        source_url="https://foo.bar",
        source_subdirectory="baz",
    )
    a2 = Package(
        a1.name,
        a1.version,
        source_type="git",
        source_url="https://foo.bar",
        source_subdirectory="qux",
    )
    a3 = Package(
        a1.name,
        a1.version,
        source_type="git",
        source_url="https://foo.bar",
        source_subdirectory="baz",
    )
    a4 = Package(a1.name, a1.version, source_type="git")

    assert a1 == a3
    assert a1 != a2
    assert a2 != a3
    assert a1 != a4
    assert a2 != a4


def test_complete_name() -> None:
    assert Package("foo", "1.2.3").complete_name == "foo"
    assert (
        Package("foo", "1.2.3", features=["baz", "bar"]).complete_name == "foo[bar,baz]"
    )


def test_to_dependency() -> None:
    package = Package("foo", "1.2.3")
    dep = package.to_dependency()

    assert dep.name == "foo"
    assert dep.constraint == package.version


def test_to_dependency_with_python_constraint() -> None:
    package = Package("foo", "1.2.3")
    package.python_versions = ">=3.6"
    dep = package.to_dependency()

    assert dep.name == "foo"
    assert dep.constraint == package.version
    assert dep.python_versions == ">=3.6"


def test_to_dependency_with_features() -> None:
    package = Package("foo", "1.2.3", features=["baz", "bar"])
    dep = package.to_dependency()

    assert dep.name == "foo"
    assert dep.constraint == package.version
    assert dep.features == frozenset({"bar", "baz"})


def test_to_dependency_for_directory() -> None:
    path = Path(__file__).parent.parent.joinpath("fixtures/simple_project")
    package = Package(
        "foo",
        "1.2.3",
        source_type="directory",
        source_url=path.as_posix(),
        features=["baz", "bar"],
    )
    dep = package.to_dependency()

    assert dep.name == "foo"
    assert dep.constraint == package.version
    assert dep.features == frozenset({"bar", "baz"})
    assert dep.is_directory()
    dep = cast(DirectoryDependency, dep)
    assert dep.path == path
    assert dep.source_type == "directory"
    assert dep.source_url == path.as_posix()


def test_to_dependency_for_file() -> None:
    path = Path(__file__).parent.parent.joinpath(
        "fixtures/distributions/demo-0.1.0.tar.gz"
    )
    package = Package(
        "foo",
        "1.2.3",
        source_type="file",
        source_url=path.as_posix(),
        features=["baz", "bar"],
    )
    dep = package.to_dependency()

    assert dep.name == "foo"
    assert dep.constraint == package.version
    assert dep.features == frozenset({"bar", "baz"})
    assert dep.is_file()
    dep = cast(FileDependency, dep)
    assert dep.path == path
    assert dep.source_type == "file"
    assert dep.source_url == path.as_posix()


def test_to_dependency_for_url() -> None:
    package = Package(
        "foo",
        "1.2.3",
        source_type="url",
        source_url="https://example.com/path.tar.gz",
        features=["baz", "bar"],
    )
    dep = package.to_dependency()

    assert dep.name == "foo"
    assert dep.constraint == package.version
    assert dep.features == frozenset({"bar", "baz"})
    assert dep.is_url()
    dep = cast(URLDependency, dep)
    assert dep.url == "https://example.com/path.tar.gz"
    assert dep.source_type == "url"
    assert dep.source_url == "https://example.com/path.tar.gz"


def test_to_dependency_for_vcs() -> None:
    package = Package(
        "foo",
        "1.2.3",
        source_type="git",
        source_url="https://github.com/foo/foo.git",
        source_reference="master",
        source_resolved_reference="123456",
        source_subdirectory="baz",
        features=["baz", "bar"],
    )
    dep = package.to_dependency()

    assert dep.name == "foo"
    assert dep.constraint == package.version
    assert dep.features == frozenset({"bar", "baz"})
    assert dep.is_vcs()
    dep = cast(VCSDependency, dep)
    assert dep.source_type == "git"
    assert dep.source == "https://github.com/foo/foo.git"
    assert dep.reference == "master"
    assert dep.source_reference == "master"
    assert dep.source_resolved_reference == "123456"
    assert dep.directory == "baz"
    assert dep.source_subdirectory == "baz"


def test_package_clone(f: Factory) -> None:
    # TODO(nic): this test is not future-proof, in that any attributes added
    #  to the Package object and not filled out in this test setup might
    #  cause comparisons to match that otherwise should not.  A factory method
    #  to create a Package object with all fields fully randomized would be the
    #  most rigorous test for this, but that's likely overkill.
    p = Package(
        "lol_wut",
        "3.141.5926535",
        pretty_version="③.⑭.⑮",
        source_type="git",
        source_url="http://some.url",
        source_reference="fe4d2adabf3feb5d32b70ab5c105285fa713b10c",
        source_resolved_reference="fe4d2adabf3feb5d32b70ab5c105285fa713b10c",
        features=["abc", "def"],
        develop=random.choice((True, False)),
    )
    p.add_dependency(Factory.create_dependency("foo", "^1.2.3"))
    p.add_dependency(Factory.create_dependency("foo", "^1.2.3", groups=["dev"]))
    p.files = (["file1", "file2", "file3"],)  # type: ignore[assignment]
    p.homepage = "https://some.other.url"
    p.repository_url = "http://bug.farm"
    p.documentation_url = "http://lorem.ipsum/dolor/sit.amet"
    p2 = p.clone()

    assert p == p2
    assert p.__dict__ == p2.__dict__
    assert len(p2.requires) == 1
    assert len(p2.all_requires) == 2


def test_dependency_groups(package_with_groups: Package) -> None:
    assert len(package_with_groups.requires) == 2
    assert len(package_with_groups.all_requires) == 4


def test_without_dependency_groups(package_with_groups: Package) -> None:
    package = package_with_groups.without_dependency_groups(["dev"])

    assert len(package.requires) == 2
    assert len(package.all_requires) == 3

    package = package_with_groups.without_dependency_groups(["dev", "optional"])

    assert len(package.requires) == 2
    assert len(package.all_requires) == 2


def test_with_dependency_groups(package_with_groups: Package) -> None:
    package = package_with_groups.with_dependency_groups([])

    assert len(package.requires) == 2
    assert len(package.all_requires) == 3

    package = package_with_groups.with_dependency_groups(["optional"])

    assert len(package.requires) == 2
    assert len(package.all_requires) == 4


def test_without_optional_dependency_groups(package_with_groups: Package) -> None:
    package = package_with_groups.without_optional_dependency_groups()

    assert len(package.requires) == 2
    assert len(package.all_requires) == 3


def test_only_with_dependency_groups(package_with_groups: Package) -> None:
    package = package_with_groups.with_dependency_groups(["dev"], only=True)

    assert len(package.requires) == 0
    assert len(package.all_requires) == 1

    package = package_with_groups.with_dependency_groups(["dev", "optional"], only=True)

    assert len(package.requires) == 0
    assert len(package.all_requires) == 2

    package = package_with_groups.with_dependency_groups(["main"], only=True)

    assert len(package.requires) == 2
    assert len(package.all_requires) == 2


def test_get_readme_property_with_multiple_readme_files() -> None:
    package = Package("foo", "0.1.0")

    package.readmes = (Path("README.md"), Path("HISTORY.md"))
    with pytest.deprecated_call():
        assert package.readme == Path("README.md")


def test_set_readme_property() -> None:
    package = Package("foo", "0.1.0")

    with pytest.deprecated_call():
        package.readme = Path("README.md")

    assert package.readmes == (Path("README.md"),)
    with pytest.deprecated_call():
        assert package.readme == Path("README.md")


@pytest.mark.parametrize(
    ("package", "dependency", "ignore_source_type", "result"),
    [
        (Package("foo", "0.1.0"), Dependency("foo", ">=0.1.0"), False, True),
        (Package("foo", "0.1.0"), Dependency("foo", "<0.1.0"), False, False),
        (
            Package("foo", "0.1.0"),
            Dependency("foo", ">=0.1.0", source_type="git"),
            False,
            False,
        ),
        (
            Package("foo", "0.1.0"),
            Dependency("foo", ">=0.1.0", source_type="git"),
            True,
            True,
        ),
        (
            Package("foo", "0.1.0"),
            Dependency("foo", "<0.1.0", source_type="git"),
            True,
            False,
        ),
    ],
)
def test_package_satisfies(
    package: Package, dependency: Dependency, ignore_source_type: bool, result: bool
) -> None:
    assert package.satisfies(dependency, ignore_source_type) == result
