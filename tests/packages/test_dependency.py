import pytest

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.package import Package
from poetry.core.version.markers import parse_marker


def test_accepts():
    dependency = Dependency("A", "^1.0")
    package = Package("A", "1.4")

    assert dependency.accepts(package)


@pytest.mark.parametrize(
    "constraint,result",
    [
        ("^1.0", False),
        ("^1.0.dev0", True),
        ("^1.0.0", False),
        ("^1.0.0.dev0", True),
        ("^1.0.0.alpha0", True),
        ("^1.0.0.alpha0+local", True),
        ("^1.0.0.rc0+local", True),
        ("^1.0.0-1", False),
    ],
)
def test_allows_prerelease(constraint, result):
    assert Dependency("A", constraint).allows_prereleases() == result


def test_accepts_prerelease():
    dependency = Dependency("A", "^1.0", allows_prereleases=True)
    package = Package("A", "1.4-beta.1")

    assert dependency.accepts(package)


def test_accepts_python_versions():
    dependency = Dependency("A", "^1.0")
    dependency.python_versions = "^3.6"
    package = Package("A", "1.4")
    package.python_versions = "~3.6"

    assert dependency.accepts(package)


def test_accepts_fails_with_different_names():
    dependency = Dependency("A", "^1.0")
    package = Package("B", "1.4")

    assert not dependency.accepts(package)


def test_accepts_fails_with_version_mismatch():
    dependency = Dependency("A", "~1.0")
    package = Package("B", "1.4")

    assert not dependency.accepts(package)


def test_accepts_fails_with_prerelease_mismatch():
    dependency = Dependency("A", "^1.0")
    package = Package("B", "1.4-beta.1")

    assert not dependency.accepts(package)


def test_accepts_fails_with_python_versions_mismatch():
    dependency = Dependency("A", "^1.0")
    dependency.python_versions = "^3.6"
    package = Package("B", "1.4")
    package.python_versions = "~3.5"

    assert not dependency.accepts(package)


def test_to_pep_508():
    dependency = Dependency("Django", "^1.23")

    result = dependency.to_pep_508()
    assert result == "Django (>=1.23,<2.0)"

    dependency = Dependency("Django", "^1.23")
    dependency.python_versions = "~2.7 || ^3.6"

    result = dependency.to_pep_508()
    assert (
        result == "Django (>=1.23,<2.0); "
        'python_version >= "2.7" and python_version < "2.8" '
        'or python_version >= "3.6" and python_version < "4.0"'
    )


def test_to_pep_508_wilcard():
    dependency = Dependency("Django", "*")

    result = dependency.to_pep_508()
    assert result == "Django"


def test_to_pep_508_in_extras():
    dependency = Dependency("Django", "^1.23")
    dependency.in_extras.append("foo")

    result = dependency.to_pep_508()
    assert result == 'Django (>=1.23,<2.0); extra == "foo"'

    result = dependency.to_pep_508(with_extras=False)
    assert result == "Django (>=1.23,<2.0)"

    dependency.in_extras.append("bar")

    result = dependency.to_pep_508()
    assert result == 'Django (>=1.23,<2.0); extra == "foo" or extra == "bar"'

    dependency.python_versions = "~2.7 || ^3.6"

    result = dependency.to_pep_508()
    assert result == (
        "Django (>=1.23,<2.0); "
        "("
        'python_version >= "2.7" and python_version < "2.8" '
        'or python_version >= "3.6" and python_version < "4.0"'
        ") "
        'and (extra == "foo" or extra == "bar")'
    )

    result = dependency.to_pep_508(with_extras=False)
    assert result == (
        "Django (>=1.23,<2.0); "
        'python_version >= "2.7" and python_version < "2.8" '
        'or python_version >= "3.6" and python_version < "4.0"'
    )


def test_to_pep_508_in_extras_parsed():
    dependency = Dependency.create_from_pep_508(
        'foo[bar] (>=1.23,<2.0) ; extra == "baz"'
    )

    result = dependency.to_pep_508()
    assert result == 'foo[bar] (>=1.23,<2.0); extra == "baz"'

    result = dependency.to_pep_508(with_extras=False)
    assert result == "foo[bar] (>=1.23,<2.0)"


def test_to_pep_508_with_single_version_excluded():
    dependency = Dependency("foo", "!=1.2.3")

    assert "foo (!=1.2.3)" == dependency.to_pep_508()


@pytest.mark.parametrize(
    "python_versions, marker",
    [
        (">=3.5,<3.5.4", 'python_version >= "3.5" and python_full_version < "3.5.4"'),
        (">=3.5.4,<3.6", 'python_full_version >= "3.5.4" and python_version < "3.6"'),
        ("<3.5.4", 'python_full_version < "3.5.4"'),
        (">=3.5.4", 'python_full_version >= "3.5.4"'),
        ("== 3.5.4", 'python_full_version == "3.5.4"'),
    ],
)
def test_to_pep_508_with_patch_python_version(python_versions, marker):
    dependency = Dependency("Django", "^1.23")
    dependency.python_versions = python_versions

    expected = "Django (>=1.23,<2.0); {}".format(marker)

    assert expected == dependency.to_pep_508()
    assert marker == str(dependency.marker)


def test_to_pep_508_tilde():
    dependency = Dependency("foo", "~1.2.3")

    assert "foo (>=1.2.3,<1.3.0)" == dependency.to_pep_508()

    dependency = Dependency("foo", "~1.2")

    assert "foo (>=1.2,<1.3)" == dependency.to_pep_508()

    dependency = Dependency("foo", "~0.2.3")

    assert "foo (>=0.2.3,<0.3.0)" == dependency.to_pep_508()

    dependency = Dependency("foo", "~0.2")

    assert "foo (>=0.2,<0.3)" == dependency.to_pep_508()


def test_to_pep_508_caret():
    dependency = Dependency("foo", "^1.2.3")

    assert "foo (>=1.2.3,<2.0.0)" == dependency.to_pep_508()

    dependency = Dependency("foo", "^1.2")

    assert "foo (>=1.2,<2.0)" == dependency.to_pep_508()

    dependency = Dependency("foo", "^0.2.3")

    assert "foo (>=0.2.3,<0.3.0)" == dependency.to_pep_508()

    dependency = Dependency("foo", "^0.2")

    assert "foo (>=0.2,<0.3)" == dependency.to_pep_508()


def test_to_pep_508_combination():
    dependency = Dependency("foo", "^1.2,!=1.3.5")

    assert "foo (>=1.2,<2.0,!=1.3.5)" == dependency.to_pep_508()

    dependency = Dependency("foo", "~1.2,!=1.2.5")

    assert "foo (>=1.2,<1.3,!=1.2.5)" == dependency.to_pep_508()


def test_complete_name():
    assert "foo" == Dependency("foo", ">=1.2.3").complete_name
    assert (
        "foo[bar,baz]"
        == Dependency("foo", ">=1.2.3", extras=["baz", "bar"]).complete_name
    )


@pytest.mark.parametrize(
    "name,constraint,extras,expected",
    [
        ("A", ">2.7,<3.0", None, "A (>2.7,<3.0)"),
        ("A", ">2.7,<3.0", ["x"], "A[x] (>2.7,<3.0)"),
        ("A", ">=1.6.5,<1.8.0 || >1.8.0,<3.1.0", None, "A (>=1.6.5,!=1.8.0,<3.1.0)"),
        (
            "A",
            ">=1.6.5,<1.8.0 || >1.8.0,<3.1.0",
            ["x"],
            "A[x] (>=1.6.5,!=1.8.0,<3.1.0)",
        ),
    ],
)
def test_dependency_string_representation(name, constraint, extras, expected):
    dependency = Dependency(name=name, constraint=constraint, extras=extras)
    assert str(dependency) == expected


def test_with_constraint():
    dependency = Dependency(
        "foo",
        "^1.2.3",
        optional=True,
        groups=["dev"],
        allows_prereleases=True,
        extras=["bar", "baz"],
    )
    dependency.marker = parse_marker(
        'python_version >= "3.6" and python_version < "4.0"'
    )
    dependency.transitive_marker = parse_marker(
        'python_version >= "3.7" and python_version < "4.0"'
    )
    dependency.python_versions = "^3.6"
    dependency.transitive_python_versions = "^3.7"

    new = dependency.with_constraint("^1.2.6")

    assert new.name == dependency.name
    assert str(new.constraint) == ">=1.2.6,<2.0.0"
    assert new.is_optional()
    assert new.groups == frozenset(["dev"])
    assert new.allows_prereleases()
    assert set(new.extras) == {"bar", "baz"}
    assert new.marker == dependency.marker
    assert new.transitive_marker == dependency.transitive_marker
    assert new.python_constraint == dependency.python_constraint
    assert new.transitive_python_constraint == dependency.transitive_python_constraint
