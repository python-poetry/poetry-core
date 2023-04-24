from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from poetry.core.constraints.version import EmptyConstraint
from poetry.core.constraints.version import Version
from poetry.core.constraints.version import VersionRange
from poetry.core.version.exceptions import InvalidVersion
from poetry.core.version.pep440 import ReleaseTag


if TYPE_CHECKING:
    from poetry.core.constraints.version import VersionConstraint


@pytest.mark.parametrize(
    "text,version",
    [
        ("1.0.0", Version.from_parts(1, 0, 0)),
        ("1", Version.from_parts(1, 0, 0)),
        ("1.0", Version.from_parts(1, 0, 0)),
        ("1b1", Version.from_parts(1, 0, 0, pre=ReleaseTag("beta", 1))),
        ("1.0b1", Version.from_parts(1, 0, 0, pre=ReleaseTag("beta", 1))),
        ("1.0.0b1", Version.from_parts(1, 0, 0, pre=ReleaseTag("beta", 1))),
        ("1.0.0-b1", Version.from_parts(1, 0, 0, pre=ReleaseTag("beta", 1))),
        ("1.0.0-beta.1", Version.from_parts(1, 0, 0, pre=ReleaseTag("beta", 1))),
        ("1.0.0+1", Version.from_parts(1, 0, 0, local=1)),
        ("1.0.0-1", Version.from_parts(1, 0, 0, post=ReleaseTag("post", 1))),
        ("1.0.0.0", Version.from_parts(1, 0, 0, extra=0)),
        ("1.0.0-post", Version.from_parts(1, 0, 0, post=ReleaseTag("post"))),
        ("1.0.0-post1", Version.from_parts(1, 0, 0, post=ReleaseTag("post", 1))),
        ("0.6c", Version.from_parts(0, 6, 0, pre=ReleaseTag("rc", 0))),
        ("0.6pre", Version.from_parts(0, 6, 0, pre=ReleaseTag("preview", 0))),
        ("1!2.3.4", Version.from_parts(2, 3, 4, epoch=1)),
    ],
)
def test_parse_valid(text: str, version: Version) -> None:
    parsed = Version.parse(text)

    assert parsed == version
    assert parsed.text == text


@pytest.mark.parametrize("value", [None, "example"])
def test_parse_invalid(value: str | None) -> None:
    with pytest.raises(InvalidVersion):
        Version.parse(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", "1"),
        ("1.2", "1.2"),
        ("1.2.3", "1.2.3"),
        ("2!1.2.3", "2!1.2.3"),
        ("1.2.3+local", "1.2.3+local"),
        ("1.2.3.4", "1.2.3.4"),
        ("1.dev0", "1"),
        ("1.2dev0", "1.2"),
        ("1.2.3dev0", "1.2.3"),
        ("1.2.3.4dev0", "1.2.3.4"),
        ("1.post1", "1.post1"),
        ("1.2.post1", "1.2.post1"),
        ("1.2.3.post1", "1.2.3.post1"),
        ("1.post1.dev0", "1.post1"),
        ("1.2.post1.dev0", "1.2.post1"),
        ("1.2.3.post1.dev0", "1.2.3.post1"),
        ("1.a1", "1"),
        ("1.2a1", "1.2"),
        ("1.2.3a1", "1.2.3"),
        ("1.2.3.4a1", "1.2.3.4"),
        ("1.a1.post2", "1"),
        ("1.2a1.post2", "1.2"),
        ("1.2.3a1.post2", "1.2.3"),
        ("1.2.3.4a1.post2", "1.2.3.4"),
        ("1.a1.post2.dev0", "1"),
        ("1.2a1.post2.dev0", "1.2"),
        ("1.2.3a1.post2.dev0", "1.2.3"),
        ("1.2.3.4a1.post2.dev0", "1.2.3.4"),
    ],
)
def test_stable(version: str, expected: str) -> None:
    subject = Version.parse(version)

    assert subject.stable.text == expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", "2"),
        ("1.2", "2.0"),
        ("1.2.3", "2.0.0"),
        ("2!1.2.3", "2!2.0.0"),
        ("1.2.3+local", "2.0.0"),
        ("1.2.3.4", "2.0.0.0"),
        ("1.dev0", "2"),
        ("1.2dev0", "2.0"),
        ("1.2.3dev0", "2.0.0"),
        ("1.2.3.4dev0", "2.0.0.0"),
        ("1.post1", "2"),
        ("1.2.post1", "2.0"),
        ("1.2.3.post1", "2.0.0"),
        ("1.post1.dev0", "2"),
        ("1.2.post1.dev0", "2.0"),
        ("1.2.3.post1.dev0", "2.0.0"),
        ("2.a1", "3"),
        ("2.2a1", "3.0"),
        ("2.2.3a1", "3.0.0"),
        ("2.2.3.4a1", "3.0.0.0"),
        ("2.a1.post2", "3"),
        ("2.2a1.post2", "3.0"),
        ("2.2.3a1.post2", "3.0.0"),
        ("2.2.3.4a1.post2", "3.0.0.0"),
        ("2.a1.post2.dev0", "3"),
        ("2.2a1.post2.dev0", "3.0"),
        ("2.2.3a1.post2.dev0", "3.0.0"),
        ("2.2.3.4a1.post2.dev0", "3.0.0.0"),
    ],
)
def test_next_breaking_for_major_over_0_results_into_next_major_and_preserves_precision(
    version: str, expected: str
) -> None:
    subject = Version.parse(version)

    assert subject.next_breaking().text == expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("0", "1"),
        ("0.0", "0.1"),
        ("0.2", "0.3"),
        ("0.2.3", "0.3.0"),
        ("2!0.2.3", "2!0.3.0"),
        ("0.2.3+local", "0.3.0"),
        ("0.2.3.4", "0.3.0.0"),
        ("0.0.3.4", "0.0.4.0"),
        ("0.dev0", "1"),
        ("0.0dev0", "0.1"),
        ("0.2dev0", "0.3"),
        ("0.2.3dev0", "0.3.0"),
        ("0.0.3dev0", "0.0.4"),
        ("0.post1", "1"),
        ("0.0.post1", "0.1"),
        ("0.2.post1", "0.3"),
        ("0.2.3.post1", "0.3.0"),
        ("0.0.3.post1", "0.0.4"),
        ("0.post1.dev0", "1"),
        ("0.0.post1.dev0", "0.1"),
        ("0.2.post1.dev0", "0.3"),
        ("0.2.3.post1.dev0", "0.3.0"),
        ("0.0.3.post1.dev0", "0.0.4"),
        ("0.a1", "1"),
        ("0.0a1", "0.1"),
        ("0.2a1", "0.3"),
        ("0.2.3a1", "0.3.0"),
        ("0.2.3.4a1", "0.3.0.0"),
        ("0.0.3.4a1", "0.0.4.0"),
        ("0.a1.post2", "1"),
        ("0.0a1.post2", "0.1"),
        ("0.2a1.post2", "0.3"),
        ("0.2.3a1.post2", "0.3.0"),
        ("0.2.3.4a1.post2", "0.3.0.0"),
        ("0.0.3.4a1.post2", "0.0.4.0"),
        ("0.a1.post2.dev0", "1"),
        ("0.0a1.post2.dev0", "0.1"),
        ("0.2a1.post2.dev0", "0.3"),
        ("0.2.3a1.post2.dev0", "0.3.0"),
        ("0.2.3.4a1.post2.dev0", "0.3.0.0"),
        ("0.0.3.4a1.post2.dev0", "0.0.4.0"),
        ("0-alpha.1", "1"),
        ("0.0-alpha.1", "0.1"),
        ("0.2-alpha.1", "0.3"),
        ("0.0.1-alpha.2", "0.0.2"),
        ("0.1.2-alpha.1", "0.2.0"),
    ],
)
def test_next_breaking_for_major_0_is_treated_with_more_care_and_preserves_precision(
    version: str, expected: str
) -> None:
    subject = Version.parse(version)

    assert subject.next_breaking().text == expected


@pytest.mark.parametrize(
    "versions",
    [
        [
            "1.0.0-alpha",
            "1.0.0-alpha.1",
            "1.0.0-beta.2",
            "1.0.0-beta.11",
            "1.0.0-rc.1",
            "1.0.0-rc.1+build.1",
            "1.0.0",
            "1.0.0+0.3.7",
            "1.3.7+build",
            "1.3.7+build.2.b8f12d7",
            "1.3.7+build.11.e0f985a",
            "2.0.0",
            "2.1.0",
            "2.2.0",
            "2.11.0",
            "2.11.1",
        ],
        # PEP 440 example comparisons
        [
            "1.0.dev456",
            "1.0.dev456+local",
            "1.0.dev457",
            "1.0a1",
            "1.0a1+local",
            "1.0a2.dev456",
            "1.0a2.dev456+local",
            "1.0a2.dev457",
            "1.0a2",
            "1.0a12.dev455",
            "1.0a12",
            "1.0b1.dev456",
            "1.0b2",
            "1.0b2.post345.dev456",
            "1.0b2.post345",
            "1.0rc1.dev456",
            "1.0rc1",
            "1.0",
            "1.0+local",
            "1.0.post456.dev34",
            "1.0.post456.dev34+local",
            "1.0.post456.dev35",
            "1.0.post456",
            "1.0.post456+local",
            "1.0.post457",
            "1.1.dev1",
        ],
        # PEP 440 local versions
        [
            "1.0",
            # Comparison and ordering of local versions considers each segment
            # of the local version (divided by a .) separately.
            "1.0+abc.2",
            # If a segment consists entirely of ASCII digits then
            # that section should be considered an integer for comparison purposes
            "1.0+abc.10",
            # and if a segment contains any ASCII letters then
            # that segment is compared lexicographically with case insensitivity.
            "1.0+ABD.1",
            # When comparing a numeric and lexicographic segment, the numeric section
            # always compares as greater than the lexicographic segment.
            "1.0+5",
            # Additionally, a local version with a great number of segments will always
            # compare as greater than a local version with fewer segments,
            # as long as the shorter local version's segments match the beginning of
            # the longer local version's segments exactly.
            "1.0+5.0",
            "1.1",
        ],
    ],
)
def test_comparison(versions: list[str]) -> None:
    for i in range(len(versions)):
        for j in range(len(versions)):
            a = Version.parse(versions[i])
            b = Version.parse(versions[j])

            assert (a < b) == (i < j)
            assert (a > b) == (i > j)
            assert (a <= b) == (i <= j)
            assert (a >= b) == (i >= j)
            assert (a == b) == (i == j)
            assert (a != b) == (i != j)


def test_equality() -> None:
    assert Version.parse("1.2.3") == Version.parse("01.2.3")
    assert Version.parse("1.2.3") == Version.parse("1.02.3")
    assert Version.parse("1.2.3") == Version.parse("1.2.03")
    assert Version.parse("1.2.3-1") == Version.parse("1.2.3-01")
    assert Version.parse("1.2.3+1") == Version.parse("1.2.3+01")


def test_allows() -> None:
    v = Version.parse("1.2.3")
    assert v.allows(v)
    assert not v.allows(Version.parse("1.2"))
    assert not v.allows(Version.parse("2.2.3"))
    assert not v.allows(Version.parse("1.3.3"))
    assert not v.allows(Version.parse("1.2.4"))
    assert not v.allows(Version.parse("1.2.3-dev"))
    assert not v.allows(Version.parse("1.2.3-1"))
    assert not v.allows(Version.parse("1.2.3-1+build"))
    assert v.allows(Version.parse("1.2.3+build"))


@pytest.mark.parametrize(
    ("version1", "version2"),
    [
        ("1", "1.0"),
        ("1", "1.0.0"),
        ("1", "1.0.0.0"),
        ("1.2", "1.2.0"),
        ("1.2", "1.2.0.0"),
        ("1.2", "1.2.0.0.0"),
        ("1.2.3", "1.2.3.0"),
        ("1.2.3", "1.2.3.0.0"),
        ("1.2.3.4", "1.2.3.4.0"),
        ("1.2.3.4", "1.2.3.4.0.0"),
        ("1.2.3.4a1", "1.2.3.4.0a1"),
    ],
)
def test_allows_zero_padding(version1: str, version2: str) -> None:
    v1 = Version.parse(version1)
    v2 = Version.parse(version2)
    assert v1.allows(v2)
    assert v2.allows(v1)
    assert v1.allows_all(v2)
    assert v2.allows_all(v1)
    assert v1.allows_any(v2)
    assert v2.allows_any(v1)


def test_allows_with_local() -> None:
    v = Version.parse("1.2.3+build.1")
    assert v.allows(v)
    assert not v.allows(Version.parse("1.2.3"))
    assert not v.allows(Version.parse("1.3.3"))
    assert not v.allows(Version.parse("1.2.3-dev"))
    assert not v.allows(Version.parse("1.2.3+build.2"))
    # local version with a great number of segments will always compare as
    # greater than a local version with fewer segments
    assert not v.allows(Version.parse("1.2.3+build.1.0"))
    assert not v.allows(Version.parse("1.2.3-1"))
    assert not v.allows(Version.parse("1.2.3-1+build.1"))


def test_allows_with_post() -> None:
    v = Version.parse("1.2.3-1")
    assert v.allows(v)
    assert not v.allows(Version.parse("1.2.3"))
    assert not v.allows(Version.parse("1.2.3-2"))
    assert not v.allows(Version.parse("2.2.3"))
    assert not v.allows(Version.parse("1.2.3-dev"))
    assert not v.allows(Version.parse("1.2.3+build.2"))
    assert v.allows(Version.parse("1.2.3-1+build.1"))


def test_allows_all() -> None:
    v = Version.parse("1.2.3")

    assert v.allows_all(v)
    assert not v.allows_all(Version.parse("0.0.3"))
    assert not v.allows_all(
        VersionRange(Version.parse("1.1.4"), Version.parse("1.2.4"))
    )
    assert not v.allows_all(VersionRange())
    assert v.allows_all(EmptyConstraint())


@pytest.mark.parametrize(
    ("version1", "version2", "expected"),
    [
        (
            Version.parse("1.2.3"),
            Version.parse("1.2.3"),
            True,
        ),
        (
            Version.parse("1.2.3"),
            Version.parse("1.2.3+cpu"),
            True,
        ),
        (
            Version.parse("1.2.3+cpu"),
            Version.parse("1.2.3"),
            False,
        ),
        (
            Version.parse("1.2.3"),
            Version.parse("0.0.3"),
            False,
        ),
        (
            Version.parse("1.2.3"),
            VersionRange(Version.parse("1.1.4"), Version.parse("1.2.4")),
            True,
        ),
        (
            Version.parse("1.2.3"),
            VersionRange(),
            True,
        ),
        (
            Version.parse("1.2.3"),
            EmptyConstraint(),
            False,
        ),
    ],
)
def test_allows_any(
    version1: VersionConstraint,
    version2: VersionConstraint,
    expected: bool,
) -> None:
    actual = version1.allows_any(version2)
    assert actual == expected


@pytest.mark.parametrize(
    ("version1", "version2", "expected"),
    [
        (
            Version.parse("1.2.3"),
            Version.parse("1.1.4"),
            EmptyConstraint(),
        ),
        (
            Version.parse("1.2.3"),
            VersionRange(Version.parse("1.1.4"), Version.parse("1.2.4")),
            Version.parse("1.2.3"),
        ),
        (
            Version.parse("1.1.4"),
            VersionRange(Version.parse("1.2.3"), Version.parse("1.2.4")),
            EmptyConstraint(),
        ),
        (
            Version.parse("1.2.3"),
            Version.parse("1.2.3.post0"),
            EmptyConstraint(),
        ),
        (
            Version.parse("1.2.3"),
            Version.parse("1.2.3+local"),
            Version.parse("1.2.3+local"),
        ),
    ],
)
def test_intersect(
    version1: VersionConstraint,
    version2: VersionConstraint,
    expected: VersionConstraint,
) -> None:
    assert version1.intersect(version2) == expected
    assert version2.intersect(version1) == expected


def test_union() -> None:
    v = Version.parse("1.2.3")

    assert v.union(v) == v

    result = v.union(Version.parse("0.8.0"))
    assert result.allows(v)
    assert result.allows(Version.parse("0.8.0"))
    assert not result.allows(Version.parse("1.1.4"))

    range = VersionRange(Version.parse("1.1.4"), Version.parse("1.2.4"))
    assert v.union(range) == range

    union = Version.parse("1.1.4").union(
        VersionRange(Version.parse("1.1.4"), Version.parse("1.2.4"))
    )
    assert union == VersionRange(
        Version.parse("1.1.4"), Version.parse("1.2.4"), include_min=True
    )

    result = v.union(VersionRange(Version.parse("0.0.3"), Version.parse("1.1.4")))
    assert result.allows(v)
    assert result.allows(Version.parse("0.1.0"))


def test_difference() -> None:
    v = Version.parse("1.2.3")

    assert v.difference(v).is_empty()
    assert v.difference(Version.parse("0.8.0")) == v
    assert v.difference(
        VersionRange(Version.parse("1.1.4"), Version.parse("1.2.4"))
    ).is_empty()
    assert (
        v.difference(VersionRange(Version.parse("1.4.0"), Version.parse("3.0.0"))) == v
    )


@pytest.mark.parametrize(
    "version,normalized_version",
    [
        (  # already normalized version
            "1!2.3.4.5.6a7.post8.dev9+local1.123.abc",
            "1!2.3.4.5.6a7.post8.dev9+local1.123.abc",
        ),
        # PEP 440 Normalization
        # Case sensitivity
        ("1.1RC1", "1.1rc1"),
        # Integer Normalization
        ("00", "0"),
        ("09000", "9000"),
        ("1.0+foo0100", "1.0+foo0100"),
        # Pre-release separators
        ("1.1.a1", "1.1a1"),
        ("1.1-a1", "1.1a1"),
        ("1.1_a1", "1.1a1"),
        ("1.1a.1", "1.1a1"),
        ("1.1a-1", "1.1a1"),
        ("1.1a_1", "1.1a1"),
        # Pre-release spelling
        ("1.1alpha1", "1.1a1"),
        ("1.1beta2", "1.1b2"),
        ("1.1c3", "1.1rc3"),
        ("1.1pre4", "1.1rc4"),
        ("1.1preview5", "1.1rc5"),
        # Implicit pre-release number
        ("1.2a", "1.2a0"),
        # Post release separators
        ("1.2.post2", "1.2.post2"),
        ("1.2-post2", "1.2.post2"),
        ("1.2_post2", "1.2.post2"),
        ("1.2post.2", "1.2.post2"),
        ("1.2post-2", "1.2.post2"),
        ("1.2post_2", "1.2.post2"),
        # Post release spelling
        ("1.0-r4", "1.0.post4"),
        ("1.0-rev4", "1.0.post4"),
        # Implicit post release number
        ("1.2.post", "1.2.post0"),
        # Implicit post releases
        ("1.0-1", "1.0.post1"),
        # Development release separators
        ("1.2.dev2", "1.2.dev2"),
        ("1.2-dev2", "1.2.dev2"),
        ("1.2_dev2", "1.2.dev2"),
        ("1.2dev.2", "1.2.dev2"),
        ("1.2dev-2", "1.2.dev2"),
        ("1.2dev_2", "1.2.dev2"),
        # Implicit development release number
        ("1.2.dev", "1.2.dev0"),
        # Local version segments
        ("1.0+ubuntu-1", "1.0+ubuntu.1"),
        ("1.0+ubuntu_1", "1.0+ubuntu.1"),
        # Preceding v character
        ("v1.0", "1.0"),
        # Leading and Trailing Whitespace
        (" 1.0 ", "1.0"),
        ("\t1.0\t", "1.0"),
        ("\n1.0\n", "1.0"),
        ("\r\n1.0\r\n", "1.0"),
        ("\f1.0\f", "1.0"),
        ("\v1.0\v", "1.0"),
    ],
)
def test_to_string_normalizes(version: str, normalized_version: str) -> None:
    assert Version.parse(version).to_string() == normalized_version
