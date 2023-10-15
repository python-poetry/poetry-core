from __future__ import annotations

from contextlib import AbstractContextManager
from contextlib import nullcontext
from typing import Any

import pytest

from packaging.utils import canonicalize_name

from poetry.core.constraints.version.exceptions import ParseConstraintError
from poetry.core.packages.dependency import Dependency
from poetry.core.version.markers import InvalidMarker
from poetry.core.version.markers import parse_marker
from poetry.core.version.requirements import InvalidRequirement


@pytest.mark.parametrize(
    "constraint",
    [
        "^1.0",
        "^1.0.dev0",
        "^1.0.0",
        "^1.0.0.dev0",
        "^1.0.0.alpha0",
        "^1.0.0.alpha0+local",
        "^1.0.0.rc0+local",
        "^1.0.0-1",
    ],
)
@pytest.mark.parametrize("allows_prereleases", [False, True])
def test_allows_prerelease(constraint: str, allows_prereleases: bool) -> None:
    dependency = Dependency("A", constraint, allows_prereleases=allows_prereleases)
    assert dependency.allows_prereleases() == allows_prereleases


def test_to_pep_508() -> None:
    dependency = Dependency("Django", "^1.23")

    result = dependency.to_pep_508()
    assert result == "Django (>=1.23,<2.0)"

    dependency = Dependency("Django", "^1.23")
    dependency.python_versions = "~2.7 || ^3.6"

    result = dependency.to_pep_508()
    assert (
        result
        == "Django (>=1.23,<2.0) ; "
        'python_version >= "2.7" and python_version < "2.8" '
        'or python_version >= "3.6" and python_version < "4.0"'
    )


def test_to_pep_508_wilcard() -> None:
    dependency = Dependency("Django", "*")

    result = dependency.to_pep_508()
    assert result == "Django"


def test_to_pep_508_in_extras() -> None:
    dependency = Dependency("Django", "^1.23")
    dependency.in_extras.append(canonicalize_name("foo"))

    result = dependency.to_pep_508()
    assert result == 'Django (>=1.23,<2.0) ; extra == "foo"'

    result = dependency.to_pep_508(with_extras=False)
    assert result == "Django (>=1.23,<2.0)"

    dependency.in_extras.append(canonicalize_name("bar"))

    result = dependency.to_pep_508()
    assert result == 'Django (>=1.23,<2.0) ; extra == "foo" or extra == "bar"'

    dependency.python_versions = "~2.7 || ^3.6"

    result = dependency.to_pep_508()
    assert (
        result
        == "Django (>=1.23,<2.0) ; "
        "("
        'python_version >= "2.7" and python_version < "2.8" '
        'or python_version >= "3.6" and python_version < "4.0"'
        ") "
        'and (extra == "foo" or extra == "bar")'
    )

    result = dependency.to_pep_508(with_extras=False)
    assert (
        result
        == "Django (>=1.23,<2.0) ; "
        'python_version >= "2.7" and python_version < "2.8" '
        'or python_version >= "3.6" and python_version < "4.0"'
    )


def test_to_pep_508_in_extras_parsed() -> None:
    dependency = Dependency.create_from_pep_508(
        'foo[baz,bar] (>=1.23,<2.0) ; extra == "baz"'
    )

    result = dependency.to_pep_508()
    assert result == 'foo[bar,baz] (>=1.23,<2.0) ; extra == "baz"'

    result = dependency.to_pep_508(with_extras=False)
    assert result == "foo[bar,baz] (>=1.23,<2.0)"


@pytest.mark.parametrize(
    ("exclusion", "expected"),
    [
        ("!=1.2.3", "!=1.2.3"),
        ("!=1.2.*", "!=1.2.*"),
        ("<2.0 || >=2.1.dev0", "!=2.0.*"),
    ],
)
def test_to_pep_508_with_excluded_versions(exclusion: str, expected: str) -> None:
    dependency = Dependency("foo", exclusion)

    assert dependency.to_pep_508() == f"foo ({expected})"


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
def test_to_pep_508_with_patch_python_version(
    python_versions: str, marker: str
) -> None:
    dependency = Dependency("Django", "^1.23")
    dependency.python_versions = python_versions

    expected = f"Django (>=1.23,<2.0) ; {marker}"

    assert dependency.to_pep_508() == expected
    assert dependency.to_pep_508(resolved=True) == expected
    assert str(dependency.marker) == marker


def test_to_pep_508_tilde() -> None:
    dependency = Dependency("foo", "~1.2.3")

    assert dependency.to_pep_508() == "foo (>=1.2.3,<1.3.0)"

    dependency = Dependency("foo", "~1.2")

    assert dependency.to_pep_508() == "foo (>=1.2,<1.3)"

    dependency = Dependency("foo", "~0.2.3")

    assert dependency.to_pep_508() == "foo (>=0.2.3,<0.3.0)"

    dependency = Dependency("foo", "~0.2")

    assert dependency.to_pep_508() == "foo (>=0.2,<0.3)"


def test_to_pep_508_caret() -> None:
    dependency = Dependency("foo", "^1.2.3")

    assert dependency.to_pep_508() == "foo (>=1.2.3,<2.0.0)"

    dependency = Dependency("foo", "^1.2")

    assert dependency.to_pep_508() == "foo (>=1.2,<2.0)"

    dependency = Dependency("foo", "^0.2.3")

    assert dependency.to_pep_508() == "foo (>=0.2.3,<0.3.0)"

    dependency = Dependency("foo", "^0.2")

    assert dependency.to_pep_508() == "foo (>=0.2,<0.3)"


def test_to_pep_508_combination() -> None:
    dependency = Dependency("foo", "^1.2,!=1.3.5")

    assert dependency.to_pep_508() == "foo (>=1.2,<2.0,!=1.3.5)"

    dependency = Dependency("foo", "~1.2,!=1.2.5")

    assert dependency.to_pep_508() == "foo (>=1.2,<1.3,!=1.2.5)"


@pytest.mark.parametrize(
    "requirement",
    [
        "enum34; extra == ':python_version < \"3.4\"'",
        "enum34; extra == \":python_version < '3.4'\"",
    ],
)
def test_to_pep_508_with_invalid_marker(requirement: str) -> None:
    with pytest.raises(InvalidMarker):
        _ = Dependency.create_from_pep_508(requirement)


@pytest.mark.parametrize(
    "requirement",
    [
        'enum34; extra == ":python_version < "3.4""',
    ],
)
def test_to_pep_508_with_invalid_requirement(requirement: str) -> None:
    with pytest.raises(InvalidRequirement):
        _ = Dependency.create_from_pep_508(requirement)


def test_complete_name() -> None:
    assert Dependency("foo", ">=1.2.3").complete_name == "foo"
    assert (
        Dependency("foo", ">=1.2.3", extras=["baz", "bar"]).complete_name
        == "foo[bar,baz]"
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
        # test single version range (wildcard)
        ("A", "==2.*", None, "A (==2.*)"),
        ("A", "==2.0.*", None, "A (==2.0.*)"),
        ("A", "==0.0.*", None, "A (==0.0.*)"),
        ("A", "==0.1.*", None, "A (==0.1.*)"),
        ("A", "==0.*", None, "A (==0.*)"),
        ("A", ">=1.0.dev0,<2", None, "A (==1.*)"),
        ("A", ">=1.dev0,<2", None, "A (==1.*)"),
        ("A", ">=1.0.dev1,<2", None, "A (>=1.0.dev1,<2)"),
        ("A", ">=1.1.dev0,<2", None, "A (>=1.1.dev0,<2)"),
        ("A", ">=1.0.dev0,<2.0.dev0", None, "A (==1.*)"),
        ("A", ">=1.0.dev0,<2.0.dev1", None, "A (>=1.0.dev0,<2.0.dev1)"),
        ("A", ">=1,<2", None, "A (>=1,<2)"),
        ("A", ">=1.0.dev0,<1.1", None, "A (==1.0.*)"),
        ("A", ">=1.0.0.0.dev0,<1.1.0.0.0", None, "A (==1.0.*)"),
        # test single version range (wildcard) exclusions
        ("A", ">=1.8,!=2.0.*", None, "A (>=1.8,!=2.0.*)"),
        ("A", "!=0.0.*", None, "A (!=0.0.*)"),
        ("A", "!=0.1.*", None, "A (!=0.1.*)"),
        ("A", "!=0.*", None, "A (!=0.*)"),
        ("A", ">=1.8,!=2.*", None, "A (>=1.8,!=2.*)"),
        ("A", ">=1.8,!=2.*.*", None, "A (>=1.8,!=2.*)"),
        ("A", ">=1.8,<2.0 || >=2.1.0.dev0", None, "A (>=1.8,!=2.0.*)"),
        ("A", ">=1.8,<2.0.0 || >=3.0.0.dev0", None, "A (>=1.8,!=2.*)"),
        ("A", ">=1.8,<2.0 || >=3.dev0", None, "A (>=1.8,!=2.*)"),
        ("A", ">=1.8,<2 || >=2.1.0.dev0", None, "A (>=1.8,!=2.0.*)"),
        ("A", ">=1.8,<2 || >=2.1.dev0", None, "A (>=1.8,!=2.0.*)"),
        ("A", ">=1.8,!=2.0.*,!=3.0.*", None, "A (>=1.8,!=2.0.*,!=3.0.*)"),
        ("A", ">=1.8.0.0,<2.0.0.0 || >=2.0.1.0.dev0", None, "A (>=1.8.0.0,!=2.0.0.*)"),
        ("A", ">=1.8.0.0,<2 || >=2.0.1.0.dev0", None, "A (>=1.8.0.0,!=2.0.0.*)"),
        # we verify that the range exclusion logic is not too eager
        ("A", ">=1.8,<2.0 || >=2.2.0", None, "A (>=1.8,<2.0 || >=2.2.0)"),
        ("A", ">=1.8,<2.0 || >=2.1.5", None, "A (>=1.8,<2.0 || >=2.1.5)"),
        ("A", ">=1.8.0.0,<2 || >=2.0.1.5", None, "A (>=1.8.0.0,<2 || >=2.0.1.5)"),
        ("A", ">=1.8.0.0,!=2.0.0.*", None, "A (>=1.8.0.0,!=2.0.0.*)"),
    ],
)
def test_dependency_string_representation(
    name: str, constraint: str, extras: list[str] | None, expected: str
) -> None:
    dependency = Dependency(name=name, constraint=constraint, extras=extras)
    assert str(dependency) == expected


def test_set_constraint_sets_pretty_constraint() -> None:
    dependency = Dependency("A", "^1.0")
    assert dependency.pretty_constraint == "^1.0"
    dependency.constraint = "^2.0"  # type: ignore[assignment]
    assert dependency.pretty_constraint == "^2.0"


def test_set_bogus_constraint_raises_exception() -> None:
    dependency = Dependency("A", "^1.0")
    with pytest.raises(ParseConstraintError):
        dependency.constraint = "^=4.5"  # type: ignore[assignment]


def test_with_constraint() -> None:
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
    with pytest.warns(DeprecationWarning):
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
    with pytest.warns(DeprecationWarning):
        assert (
            new.transitive_python_constraint == dependency.transitive_python_constraint
        )


@pytest.mark.parametrize(
    "marker, expected",
    [
        ('python_version >= "3.6" and python_version < "4.0"', ">=3.6,<4.0"),
        ('sys_platform == "linux"', "*"),
        ('python_version >= "3.9" or sys_platform == "linux"', "*"),
        ('python_version >= "3.9" and sys_platform == "linux"', ">=3.9"),
    ],
)
def test_marker_properly_sets_python_constraint(marker: str, expected: str) -> None:
    dependency = Dependency("foo", "^1.2.3")
    dependency.marker = marker  # type: ignore[assignment]
    assert str(dependency.python_constraint) == expected


def test_dependency_markers_are_the_same_as_markers() -> None:
    dependency = Dependency.create_from_pep_508('foo ; extra=="bar"')
    marker = parse_marker('extra=="bar"')

    assert dependency.marker == marker


def test_marker_properly_unsets_python_constraint() -> None:
    dependency = Dependency("foo", "^1.2.3")

    dependency.marker = 'python_version >= "3.6"'  # type: ignore[assignment]
    assert str(dependency.python_constraint) == ">=3.6"

    dependency.marker = "*"  # type: ignore[assignment]
    assert str(dependency.python_constraint) == "*"


def test_create_from_pep_508_url_with_activated_extras() -> None:
    dependency = Dependency.create_from_pep_508("name [fred,bar] @ http://foo.com")
    assert dependency.extras == {"fred", "bar"}


def test_create_from_pep_508_starting_with_digit() -> None:
    dependency = Dependency.create_from_pep_508("2captcha-python")
    assert dependency.name == "2captcha-python"


@pytest.mark.parametrize(
    "dependency1, dependency2, expected",
    [
        (Dependency("a", "1.0"), Dependency("a", "1.0"), True),
        (Dependency("a", "1.0"), Dependency("a", "1.0.1"), False),
        (Dependency("a", "1.0"), Dependency("a1", "1.0"), False),
        (Dependency("a", "1.0"), Dependency("a", "1.0", source_type="file"), False),
        # constraint is implicitly given for direct origin dependencies,
        # but might not be set
        (
            Dependency("a", "1.0", source_type="file"),
            Dependency("a", "*", source_type="file"),
            True,
        ),
        # constraint is not implicit for non direct origin dependencies
        (Dependency("a", "1.0"), Dependency("a", "*"), False),
        (
            Dependency("a", "1.0", source_type="legacy"),
            Dependency("a", "*", source_type="legacy"),
            False,
        ),
    ],
)
def test_eq(dependency1: Dependency, dependency2: Dependency, expected: bool) -> None:
    assert (dependency1 == dependency2) is expected
    assert (dependency2 == dependency1) is expected


@pytest.mark.parametrize(
    "attr_name, value",
    [
        ("constraint", "2.0"),
        ("python_versions", "<3.8"),
        ("transitive_python_versions", "<3.8"),
        ("marker", "sys_platform == 'linux'"),
        ("transitive_marker", "sys_platform == 'linux'"),
    ],
)
def test_mutable_attributes_not_in_hash(attr_name: str, value: str) -> None:
    dependency = Dependency("foo", "^1.2.3")
    ref_hash = hash(dependency)

    if attr_name == "transitive_python_versions":
        context: AbstractContextManager[Any] = pytest.warns(DeprecationWarning)
    else:
        context = nullcontext()

    with context:
        ref_value = getattr(dependency, attr_name)
    with context:
        setattr(dependency, attr_name, value)
    assert value != ref_value
    assert hash(dependency) == ref_hash
