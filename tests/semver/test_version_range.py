from __future__ import annotations

import pytest

from poetry.core.semver.empty_constraint import EmptyConstraint
from poetry.core.semver.version import Version
from poetry.core.semver.version_range import VersionRange


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
    "base,other",
    [
        pytest.param(Version.parse("3.0.0"), Version.parse("3.0.0-1"), id="post"),
        pytest.param(
            Version.parse("3.0.0"), Version.parse("3.0.0+local.1"), id="local"
        ),
    ],
)
def test_allows_post_releases_with_max(base: Version, other: Version) -> None:
    range = VersionRange(max=base, include_max=True)
    assert range.allows(other)


@pytest.mark.parametrize(
    "base,other",
    [
        pytest.param(Version.parse("3.0.0"), Version.parse("3.0.0-1"), id="post"),
        pytest.param(
            Version.parse("3.0.0"), Version.parse("3.0.0+local.1"), id="local"
        ),
    ],
)
def test_allows_post_releases_with_min(base: Version, other: Version) -> None:
    range = VersionRange(min=base, include_min=True)
    assert range.allows(other)


def test_allows_post_releases_with_post_and_local_min() -> None:
    one = Version.parse("3.0.0+local.1")
    two = Version.parse("3.0.0-1")
    three = Version.parse("3.0.0-1+local.1")
    four = Version.parse("3.0.0+local.2")

    assert VersionRange(min=one, include_min=True).allows(two)
    assert VersionRange(min=one, include_min=True).allows(three)
    assert VersionRange(min=one, include_min=True).allows(four)

    assert not VersionRange(min=two, include_min=True).allows(one)
    assert VersionRange(min=two, include_min=True).allows(three)
    assert not VersionRange(min=two, include_min=True).allows(four)

    assert not VersionRange(min=three, include_min=True).allows(one)
    assert not VersionRange(min=three, include_min=True).allows(two)
    assert not VersionRange(min=three, include_min=True).allows(four)

    assert not VersionRange(min=four, include_min=True).allows(one)
    assert VersionRange(min=four, include_min=True).allows(two)
    assert VersionRange(min=four, include_min=True).allows(three)


def test_allows_post_releases_with_post_and_local_max() -> None:
    one = Version.parse("3.0.0+local.1")
    two = Version.parse("3.0.0-1")
    three = Version.parse("3.0.0-1+local.1")
    four = Version.parse("3.0.0+local.2")

    assert VersionRange(max=one, include_max=True).allows(two)
    assert VersionRange(max=one, include_max=True).allows(three)
    assert not VersionRange(max=one, include_max=True).allows(four)

    assert VersionRange(max=two, include_max=True).allows(one)
    assert VersionRange(max=two, include_max=True).allows(three)
    assert VersionRange(max=two, include_max=True).allows(four)

    assert VersionRange(max=three, include_max=True).allows(one)
    assert VersionRange(max=three, include_max=True).allows(two)
    assert VersionRange(max=three, include_max=True).allows(four)

    assert VersionRange(max=four, include_max=True).allows(one)
    assert VersionRange(max=four, include_max=True).allows(two)
    assert VersionRange(max=four, include_max=True).allows(three)


@pytest.mark.parametrize(
    "base,one,two",
    [
        pytest.param(
            Version.parse("3.0.0"),
            Version.parse("3.0.0-1"),
            Version.parse("3.0.0-2"),
            id="post",
        ),
        pytest.param(
            Version.parse("3.0.0"),
            Version.parse("3.0.0+local.1"),
            Version.parse("3.0.0+local.2"),
            id="local",
        ),
    ],
)
def test_allows_post_releases_explicit_with_max(
    base: Version, one: Version, two: Version
) -> None:
    range = VersionRange(max=one, include_max=True)
    assert range.allows(base)
    assert not range.allows(two)

    range = VersionRange(max=two, include_max=True)
    assert range.allows(base)
    assert range.allows(one)


@pytest.mark.parametrize(
    "base,one,two",
    [
        pytest.param(
            Version.parse("3.0.0"),
            Version.parse("3.0.0-1"),
            Version.parse("3.0.0-2"),
            id="post",
        ),
        pytest.param(
            Version.parse("3.0.0"),
            Version.parse("3.0.0+local.1"),
            Version.parse("3.0.0+local.2"),
            id="local",
        ),
    ],
)
def test_allows_post_releases_explicit_with_min(
    base: Version, one: Version, two: Version
) -> None:
    range = VersionRange(min=one, include_min=True)
    assert not range.allows(base)
    assert range.allows(two)

    range = VersionRange(min=two, include_min=True)
    assert not range.allows(base)
    assert not range.allows(one)


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
        VersionRange(Version.parse("1.8.0"), Version.parse("1.9.0"), include_min=True)
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


def test_include_max_prerelease(v200: Version, v300: Version, v300b1: Version) -> None:
    result = VersionRange(v200, v300)

    assert not result.allows(v300b1)
    assert not result.allows_any(VersionRange(v300b1))
    assert not result.allows_all(VersionRange(v200, v300b1))

    result = VersionRange(v200, v300, always_include_max_prerelease=True)

    assert result.allows(v300b1)
    assert result.allows_any(VersionRange(v300b1))
    assert result.allows_all(VersionRange(v200, v300b1))
