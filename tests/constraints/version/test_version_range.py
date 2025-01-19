from __future__ import annotations

import pytest

from poetry.core.constraints.version import EmptyConstraint
from poetry.core.constraints.version import Version
from poetry.core.constraints.version import VersionRange
from poetry.core.constraints.version import parse_constraint


@pytest.fixture()
def v003() -> Version:
    return Version.parse("0.0.3")


@pytest.fixture()
def v010() -> Version:
    return Version.parse("0.1.0")


@pytest.fixture()
def v080() -> Version:
    return Version.parse("0.8.0")


@pytest.fixture()
def v072() -> Version:
    return Version.parse("0.7.2")


@pytest.fixture()
def v114() -> Version:
    return Version.parse("1.1.4")


@pytest.fixture()
def v123() -> Version:
    return Version.parse("1.2.3")


@pytest.fixture()
def v124() -> Version:
    return Version.parse("1.2.4")


@pytest.fixture()
def v130() -> Version:
    return Version.parse("1.3.0")


@pytest.fixture()
def v140() -> Version:
    return Version.parse("1.4.0")


@pytest.fixture()
def v200() -> Version:
    return Version.parse("2.0.0")


@pytest.fixture()
def v234() -> Version:
    return Version.parse("2.3.4")


@pytest.fixture()
def v250() -> Version:
    return Version.parse("2.5.0")


@pytest.fixture()
def v300() -> Version:
    return Version.parse("3.0.0")


@pytest.fixture()
def v300b1() -> Version:
    return Version.parse("3.0.0b1")


@pytest.mark.parametrize(
    ("constraint", "check_version", "allowed"),
    [
        # Inclusive ordering
        ("<=3.0.0", "3.0.0", True),
        ("<=3.0.0", "3.0.0+local.1", True),
        (">=3.0.0", "3.0.0", True),
        (">=3.0.0", "3.0.0+local.1", True),
        (">=3.0.0", "3.0.0", True),
        (">=3.0.0", "3.0.0-1", True),
        ("<=3.0.0+local.1", "3.0.0", True),
        ("<=3.0.0+local.1", "3.0.0+local.1", True),
        ("<=3.0.0+local.1", "3.0.0+local.2", False),
        ("<=3.0.0+local.1", "3.0.0-1", False),
        ("<=3.0.0+local.1", "3.0.0-1+local.1", False),
        (">=3.0.0+local.1", "3.0.0", False),
        (">=3.0.0+local.1", "3.0.0+local.1", True),
        (">=3.0.0+local.1", "3.0.0+local.2", True),
        (">=3.0.0+local.1", "3.0.0-1", True),
        (">=3.0.0+local.1", "3.0.0-1+local.1", True),
        ("<=3.0.0+local.2", "3.0.0+local.1", True),
        ("<=3.0.0+local.2", "3.0.0+local.2", True),
        (">=3.0.0+local.2", "3.0.0+local.1", False),
        (">=3.0.0+local.2", "3.0.0+local.2", True),
        (">=3.0.0+local.2", "3.0.0-1+local.1", True),
        ("<=3.0.0-1", "3.0.0", True),
        ("<=3.0.0-1", "3.0.0+local.1", True),
        ("<=3.0.0-1", "3.0.0+local.2", True),
        ("<=3.0.0-1", "3.0.0-1", True),
        ("<=3.0.0-1", "3.0.0-1+local.1", True),
        ("<=3.0.0-1", "3.0.0-2", False),
        (">=3.0.0-1", "3.0.0", False),
        (">=3.0.0-1", "3.0.0+local.1", False),
        (">=3.0.0-1", "3.0.0+local.2", False),
        (">=3.0.0-1", "3.0.0-1+local.1", True),
        (">=3.0.0-1", "3.0.0-2", True),
        ("<=3.0.0-1+local.1", "3.0.0+local.1", True),
        ("<=3.0.0-1+local.1", "3.0.0+local.2", True),
        ("<=3.0.0-1+local.1", "3.0.0-1", True),
        (">=3.0.0-1+local.1", "3.0.0+local.1", False),
        (">=3.0.0-1+local.1", "3.0.0+local.2", False),
        (">=3.0.0-1+local.1", "3.0.0-1", False),
        ("<=3.0.0-2", "3.0.0-1", True),
        ("<=3.0.0-2", "3.0.0-2", True),
        (">=3.0.0-2", "3.0.0-1", False),
        (">=3.0.0-2", "3.0.0-2", True),
        # Exclusive ordering
        (">1.7", "1.7.0", False),
        (">1.7", "1.7.1", True),
        (">1.7", "1.6.1", False),
        ("<1.7", "1.7.0", False),
        ("<1.7", "1.7.1", False),
        ("<1.7", "1.6.1", True),
        ## >V MUST NOT allow a post-release of the given version unless V itself is a post release
        (">1.7", "1.7.0.post1", False),
        (">1.7.post2", "1.7.0", False),
        (">1.7.post2", "1.7.1", True),
        (">1.7.post2", "1.7.0.post2", False),
        (">1.7.post2", "1.7.0.post3", True),
        ## >V MUST NOT match a local version of the specified version
        (">1.7.0", "1.7.0+local.1", False),
        ("<1.7.0", "1.7.0+local.1", False),  # spec does not clarify this
        ("<1.7.0+local.2", "1.7.0+local.1", False),  # spec does not clarify this
        ## <V MUST NOT allow a pre-release of the specified version unless the specified version is itself a pre-release
        ("<1.7.0", "1.7.0.rc1", False),
        ("<1.7.0.rc1", "1.7.0.rc1", False),
        ("<1.7.0.rc2", "1.7.0.rc1", True),
        # Misc. Cases
        (">=3.0.0+cuda", "3.0.0+cuda", True),
        (">=3.0.0+cpu", "3.0.0+cuda", True),  # cuda > cpu (lexicographically)
    ],
)
def test_version_ranges(constraint: str, check_version: str, allowed: bool) -> None:
    assert parse_constraint(constraint).allows(Version.parse(check_version)) == allowed


def test_allows_all(
    v123: Version, v124: Version, v140: Version, v250: Version, v300: Version
) -> None:
    assert VersionRange(v123, v250).allows_all(EmptyConstraint())

    range = VersionRange(v123, v250, include_max=True)
    assert not range.allows_all(v123)
    assert range.allows_all(v124)
    assert range.allows_all(v250)
    assert not range.allows_all(v300)


def test_allows_all_with_no_min(
    v080: Version, v140: Version, v250: Version, v300: Version
) -> None:
    range = VersionRange(max=v250)
    assert range.allows_all(VersionRange(v080, v140))
    assert not range.allows_all(VersionRange(v080, v300))
    assert range.allows_all(VersionRange(max=v140))
    assert not range.allows_all(VersionRange(max=v300))
    assert range.allows_all(range)
    assert not range.allows_all(VersionRange())


def test_allows_all_with_no_max(
    v003: Version, v010: Version, v080: Version, v140: Version
) -> None:
    range = VersionRange(min=v010)
    assert range.allows_all(VersionRange(v080, v140))
    assert not range.allows_all(VersionRange(v003, v140))
    assert range.allows_all(VersionRange(v080))
    assert not range.allows_all(VersionRange(v003))
    assert range.allows_all(range)
    assert not range.allows_all(VersionRange())


def test_allows_all_bordering_range_not_more_inclusive(
    v010: Version, v250: Version
) -> None:
    # Allows bordering range that is not more inclusive
    exclusive = VersionRange(v010, v250)
    inclusive = VersionRange(v010, v250, True, True)
    assert inclusive.allows_all(exclusive)
    assert inclusive.allows_all(inclusive)
    assert not exclusive.allows_all(inclusive)
    assert exclusive.allows_all(exclusive)


def test_allows_all_contained_unions(
    v010: Version,
    v114: Version,
    v123: Version,
    v124: Version,
    v140: Version,
    v200: Version,
    v234: Version,
) -> None:
    # Allows unions that are completely contained
    range = VersionRange(v114, v200)
    assert range.allows_all(VersionRange(v123, v124).union(v140))
    assert not range.allows_all(VersionRange(v010, v124).union(v140))
    assert not range.allows_all(VersionRange(v123, v234).union(v140))


def test_allows_any(
    v003: Version,
    v010: Version,
    v072: Version,
    v080: Version,
    v114: Version,
    v123: Version,
    v124: Version,
    v140: Version,
    v200: Version,
    v234: Version,
    v250: Version,
    v300: Version,
) -> None:
    # disallows an empty constraint
    assert not VersionRange(v123, v250).allows_any(EmptyConstraint())

    # allows allowed versions
    range = VersionRange(v123, v250, include_max=True)
    assert not range.allows_any(v123)
    assert range.allows_any(v124)
    assert range.allows_any(v250)
    assert not range.allows_any(v300)

    # with no min
    range = VersionRange(max=v200)
    assert range.allows_any(VersionRange(v140, v300))
    assert not range.allows_any(VersionRange(v234, v300))
    assert range.allows_any(VersionRange(v140))
    assert not range.allows_any(VersionRange(v234))
    assert range.allows_any(range)

    # with no max
    range = VersionRange(min=v072)
    assert range.allows_any(VersionRange(v003, v140))
    assert not range.allows_any(VersionRange(v003, v010))
    assert range.allows_any(VersionRange(max=v080))
    assert not range.allows_any(VersionRange(max=v003))
    assert range.allows_any(range)

    # with min and max
    range = VersionRange(v072, v200)
    assert range.allows_any(VersionRange(v003, v140))
    assert range.allows_any(VersionRange(v140, v300))
    assert not range.allows_any(VersionRange(v003, v010))
    assert not range.allows_any(VersionRange(v234, v300))
    assert not range.allows_any(VersionRange(max=v010))
    assert not range.allows_any(VersionRange(v234))
    assert range.allows_any(range)

    # allows a bordering range when both are inclusive
    assert not VersionRange(max=v250).allows_any(VersionRange(min=v250))
    assert not VersionRange(max=v250, include_max=True).allows_any(
        VersionRange(min=v250)
    )
    assert not VersionRange(max=v250).allows_any(
        VersionRange(min=v250, include_min=True)
    )
    assert not VersionRange(min=v250).allows_any(VersionRange(max=v250))
    assert VersionRange(max=v250, include_max=True).allows_any(
        VersionRange(min=v250, include_min=True)
    )

    # allows unions that are partially contained'
    range = VersionRange(v114, v200)
    assert range.allows_any(VersionRange(v010, v080).union(v140))
    assert range.allows_any(VersionRange(v123, v234).union(v300))
    assert not range.allows_any(VersionRange(v234, v300).union(v010))

    # pre-release min does not allow lesser than itself
    range = VersionRange(Version.parse("1.9b1"), include_min=True)
    assert not range.allows_any(
        VersionRange(Version.parse("1.8.0"), Version.parse("1.9.0b0"), include_min=True)
    )


def test_intersect(
    v114: Version,
    v123: Version,
    v124: Version,
    v200: Version,
    v250: Version,
    v300: Version,
) -> None:
    # two overlapping ranges
    assert VersionRange(v123, v250).intersect(VersionRange(v200, v300)) == VersionRange(
        v200, v250
    )

    # a non-overlapping range allows no versions
    a = VersionRange(v114, v124)
    b = VersionRange(v200, v250)
    assert a.intersect(b).is_empty()

    # adjacent ranges allow no versions if exclusive
    a = VersionRange(v114, v124)
    b = VersionRange(v124, v200)
    assert a.intersect(b).is_empty()

    # adjacent ranges allow version if inclusive
    a = VersionRange(v114, v124, include_max=True)
    b = VersionRange(v124, v200, include_min=True)
    assert a.intersect(b) == v124

    # with an open range
    open = VersionRange()
    a = VersionRange(v114, v124)
    assert open.intersect(open) == open
    assert open.intersect(a) == a

    # returns the version if the range allows it
    assert VersionRange(v114, v124).intersect(v123) == v123
    assert VersionRange(v123, v124).intersect(v114).is_empty()


def test_union(
    v003: Version,
    v010: Version,
    v072: Version,
    v080: Version,
    v114: Version,
    v123: Version,
    v124: Version,
    v130: Version,
    v140: Version,
    v200: Version,
    v234: Version,
    v250: Version,
    v300: Version,
) -> None:
    # with a version returns the range if it contains the version
    range = VersionRange(v114, v124)
    assert range.union(v123) == range

    # with a version on the edge of the range, expands the range
    range = VersionRange(v114, v124)
    assert range.union(v124) == VersionRange(v114, v124, include_max=True)
    assert range.union(v114) == VersionRange(v114, v124, include_min=True)

    # with a version allows both the range and the version if the range
    # doesn't contain the version
    result = VersionRange(v003, v114).union(v124)
    assert result.allows(v010)
    assert not result.allows(v123)
    assert result.allows(v124)

    # returns a VersionUnion for a disjoint range
    result = VersionRange(v003, v114).union(VersionRange(v130, v200))
    assert result.allows(v080)
    assert not result.allows(v123)
    assert result.allows(v140)

    # considers open ranges disjoint
    result = VersionRange(v003, v114).union(VersionRange(v114, v200))
    assert result.allows(v080)
    assert not result.allows(v114)
    assert result.allows(v140)
    result = VersionRange(v114, v200).union(VersionRange(v003, v114))
    assert result.allows(v080)
    assert not result.allows(v114)
    assert result.allows(v140)

    # returns a merged range for an overlapping range
    result = VersionRange(v003, v114).union(VersionRange(v080, v200))
    assert result == VersionRange(v003, v200)

    # considers closed ranges overlapping
    result = VersionRange(v003, v114, include_max=True).union(VersionRange(v114, v200))
    assert result == VersionRange(v003, v200)
    result = VersionRange(v003, v114).union(VersionRange(v114, v200, include_min=True))
    assert result == VersionRange(v003, v200)


@pytest.mark.parametrize(
    ("version", "spec", "expected"),
    [
        (v, s, True)
        for v, s in [
            # Test the equality operation
            ("2.0", "==2"),
            ("2.0", "==2.0"),
            ("2.0", "==2.0.0"),
            ("2.0+deadbeef", "==2"),
            ("2.0+deadbeef", "==2.0"),
            ("2.0+deadbeef", "==2.0.0"),
            ("2.0+deadbeef", "==2+deadbeef"),
            ("2.0+deadbeef", "==2.0+deadbeef"),
            ("2.0+deadbeef", "==2.0.0+deadbeef"),
            ("2.0+deadbeef.0", "==2.0.0+deadbeef.00"),
            # Test the equality operation with a prefix
            ("2.dev1", "==2.*"),
            ("2a1", "==2.*"),
            ("2a1.post1", "==2.*"),
            ("2b1", "==2.*"),
            ("2b1.dev1", "==2.*"),
            ("2c1", "==2.*"),
            ("2c1.post1.dev1", "==2.*"),
            ("2rc1", "==2.*"),
            ("2", "==2.*"),
            ("2.0", "==2.*"),
            ("2.0.0", "==2.*"),
            ("2.0.post1", "==2.0.post1.*"),
            ("2.0.post1.dev1", "==2.0.post1.*"),
            ("2.1+local.version", "==2.1.*"),
            # Test the in-equality operation
            ("2.1", "!=2"),
            ("2.1", "!=2.0"),
            ("2.0.1", "!=2"),
            ("2.0.1", "!=2.0"),
            ("2.0.1", "!=2.0.0"),
            ("2.0", "!=2.0+deadbeef"),
            # Test the in-equality operation with a prefix
            ("2.0", "!=3.*"),
            ("2.1", "!=2.0.*"),
            # Test the greater than equal operation
            ("2.0", ">=2"),
            ("2.0", ">=2.0"),
            ("2.0", ">=2.0.0"),
            ("2.0.post1", ">=2"),
            ("2.0.post1.dev1", ">=2"),
            ("3", ">=2"),
            # Test the less than equal operation
            ("2.0", "<=2"),
            ("2.0", "<=2.0"),
            ("2.0", "<=2.0.0"),
            ("2.0.dev1", "<=2"),
            ("2.0a1", "<=2"),
            ("2.0a1.dev1", "<=2"),
            ("2.0b1", "<=2"),
            ("2.0b1.post1", "<=2"),
            ("2.0c1", "<=2"),
            ("2.0c1.post1.dev1", "<=2"),
            ("2.0rc1", "<=2"),
            ("1", "<=2"),
            # Test the greater than operation
            ("3", ">2"),
            ("2.1", ">2.0"),
            ("2.0.1", ">2"),
            ("2.1.post1", ">2"),
            ("2.1+local.version", ">2"),
            # Test the less than operation
            ("1", "<2"),
            ("2.0", "<2.1"),
            ("2.0.dev0", "<2.1"),
            # Test the compatibility operation
            ("1", "~=1.0"),
            ("1.0.1", "~=1.0"),
            ("1.1", "~=1.0"),
            ("1.9999999", "~=1.0"),
            ("1.1", "~=1.0a1"),
            # Test that epochs are handled sanely
            ("2!1.0", "~=2!1.0"),
            ("2!1.0", "==2!1.*"),
            ("2!1.0", "==2!1.0"),
            ("2!1.0", "!=1.0"),
            ("1.0", "!=2!1.0"),
            ("1.0", "<=2!0.1"),
            ("2!1.0", ">=2.0"),
            ("1.0", "<2!0.1"),
            ("2!1.0", ">2.0"),
            # Test some normalization rules
            ("2.0.5", ">2.0dev"),
        ]
    ]
    + [
        (v, s, False)
        for v, s in [
            # Test the equality operation
            ("2.1", "==2"),
            ("2.1", "==2.0"),
            ("2.1", "==2.0.0"),
            ("2.0", "==2.0+deadbeef"),
            # Test the equality operation with a prefix
            ("2.0", "==3.*"),
            ("2.1", "==2.0.*"),
            # Test the in-equality operation
            ("2.0", "!=2"),
            ("2.0", "!=2.0"),
            ("2.0", "!=2.0.0"),
            ("2.0+deadbeef", "!=2"),
            ("2.0+deadbeef", "!=2.0"),
            ("2.0+deadbeef", "!=2.0.0"),
            ("2.0+deadbeef", "!=2+deadbeef"),
            ("2.0+deadbeef", "!=2.0+deadbeef"),
            ("2.0+deadbeef", "!=2.0.0+deadbeef"),
            ("2.0+deadbeef.0", "!=2.0.0+deadbeef.00"),
            # Test the in-equality operation with a prefix
            ("2.dev1", "!=2.*"),
            ("2a1", "!=2.*"),
            ("2a1.post1", "!=2.*"),
            ("2b1", "!=2.*"),
            ("2b1.dev1", "!=2.*"),
            ("2c1", "!=2.*"),
            ("2c1.post1.dev1", "!=2.*"),
            ("2rc1", "!=2.*"),
            ("2", "!=2.*"),
            ("2.0", "!=2.*"),
            ("2.0.0", "!=2.*"),
            ("2.0.post1", "!=2.0.post1.*"),
            ("2.0.post1.dev1", "!=2.0.post1.*"),
            # Test the greater than equal operation
            ("2.0.dev1", ">=2"),
            ("2.0a1", ">=2"),
            ("2.0a1.dev1", ">=2"),
            ("2.0b1", ">=2"),
            ("2.0b1.post1", ">=2"),
            ("2.0c1", ">=2"),
            ("2.0c1.post1.dev1", ">=2"),
            ("2.0rc1", ">=2"),
            ("1", ">=2"),
            # Test the less than equal operation
            ("2.0.post1", "<=2"),
            ("2.0.post1.dev1", "<=2"),
            ("3", "<=2"),
            # Test the greater than operation
            ("1", ">2"),
            ("2.0.dev1", ">2"),
            ("2.0a1", ">2"),
            ("2.0a1.post1", ">2"),
            ("2.0b1", ">2"),
            ("2.0b1.dev1", ">2"),
            ("2.0c1", ">2"),
            ("2.0c1.post1.dev1", ">2"),
            ("2.0rc1", ">2"),
            ("2.0", ">2"),
            ("2.0.post1", ">2"),
            ("2.0.post1.dev1", ">2"),
            ("2.0+local.version", ">2"),
            # Test the less than operation
            ("2.0.dev1", "<2"),
            ("2.0a1", "<2"),
            ("2.0a1.post1", "<2"),
            ("2.0b1", "<2"),
            ("2.0b2.dev1", "<2"),
            ("2.0c1", "<2"),
            ("2.0c1.post1.dev1", "<2"),
            ("2.0rc1", "<2"),
            ("2.0", "<2"),
            ("2.post1", "<2"),
            ("2.post1.dev1", "<2"),
            ("3", "<2"),
            # Test the compatibility operation
            ("2.0", "~=1.0"),
            ("1.1.0", "~=1.0.0"),
            ("1.1.post1", "~=1.0.0"),
            # Test that epochs are handled sanely
            ("1.0", "~=2!1.0"),
            ("2!1.0", "~=1.0"),
            ("2!1.0", "==1.0"),
            ("1.0", "==2!1.0"),
            ("2!1.0", "==1.*"),
            ("1.0", "==2!1.*"),
            ("2!1.0", "!=2!1.0"),
        ]
    ],
)
def test_specifiers(version: str, spec: str, expected: bool) -> None:
    """
    Test derived from
    https://github.com/pypa/packaging/blob/8b86d85797b9f26d98ecfbe0271ce4dc9495d98c/tests/test_specifiers.py#L469
    """
    constraint = parse_constraint(spec)

    v = Version.parse(version)

    if expected:
        # Test that the plain string form works
        # assert version in spec
        assert constraint.allows(v)

        # Test that the version instance form works
        # assert version in spec
        assert constraint.allows(v)
    else:
        # Test that the plain string form works
        # assert version not in spec
        assert not constraint.allows(v)

        # Test that the version instance form works
        # assert version not in spec
        assert not constraint.allows(v)


@pytest.mark.parametrize(
    ("include_min", "include_max", "expected"),
    [
        (True, False, True),
        (False, False, False),
        (False, True, False),
        (True, True, False),
    ],
)
def test_is_single_wildcard_range_include_min_include_max(
    include_min: bool, include_max: bool, expected: bool
) -> None:
    version_range = VersionRange(
        Version.parse("1.2.dev0"), Version.parse("1.3"), include_min, include_max
    )
    assert version_range.is_single_wildcard_range is expected


@pytest.mark.parametrize(
    ("min", "max", "expected"),
    [
        # simple wildcard ranges
        ("1.2.dev0", "1.3", True),
        ("1.2.dev0", "1.3.dev0", True),
        ("1.dev0", "2", True),
        ("1.2.3.4.5.dev0", "1.2.3.4.6", True),
        # simple non wilcard ranges
        (None, "1.3", False),
        ("1.2.dev0", None, False),
        (None, None, False),
        ("1.2a0", "1.3", False),
        ("1.2.post0", "1.3", False),
        ("1.2.dev0+local", "1.3", False),
        ("1.2", "1.3", False),
        ("1.2.dev1", "1.3", False),
        ("1.2.dev0", "1.3.post0.dev0", False),
        ("1.2.dev0", "1.3a0.dev0", False),
        ("1.2.dev0", "1.3.dev0+local", False),
        ("1.2.dev0", "1.3.dev1", False),
        # more complicated ranges
        ("1.dev0", "1.0.0.1", True),
        ("1.2.dev0", "1.3.0.0", True),
        ("1.2.dev0", "1.3.0.0.dev0", True),
        ("1.2.0.dev0", "1.3", True),
        ("1.2.1.dev0", "1.3.0.0", False),
        ("1.2.dev0", "1.4", False),
        ("1.2.dev0", "2.3", False),
        # post releases
        ("2.0.post1.dev0", "2.0.post2", True),
        ("2.0.post1.dev0", "2.0.post2.dev0", True),
        ("2.0.post1.dev1", "2.0.post2", False),
        ("2.0.post1.dev0", "2.0.post2.dev1", False),
        ("2.0.post1.dev0", "2.0.post3", False),
        ("2.0.post1.dev0", "2.0.post1", False),
    ],
)
def test_is_single_wildcard_range(
    min: str | None, max: str | None, expected: bool
) -> None:
    version_range = VersionRange(
        Version.parse(min) if min else None,
        Version.parse(max) if max else None,
        include_min=True,
    )
    assert version_range.is_single_wildcard_range is expected


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        # simple ranges
        ("*", "*"),
        (">1.2", ">1.2"),
        (">=1.2", ">=1.2"),
        ("<1.3", "<1.3"),
        ("<=1.3", "<=1.3"),
        (">=1.2,<1.3", ">=1.2,<1.3"),
        # wildcard ranges
        ("1.*", "==1.*"),
        ("1.0.*", "==1.0.*"),
        ("1.2.*", "==1.2.*"),
        ("1.2.3.4.5.*", "==1.2.3.4.5.*"),
        ("2.0.post1.*", "==2.0.post1.*"),
        ("2.1.post0.*", "==2.1.post0.*"),
        (">=1.dev0,<2", "==1.*"),
    ],
)
def test_str(version: str, expected: str) -> None:
    assert str(parse_constraint(version)) == expected
