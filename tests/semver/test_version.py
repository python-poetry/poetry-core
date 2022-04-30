from __future__ import annotations

import pytest

from poetry.core.semver.empty_constraint import EmptyConstraint
from poetry.core.semver.version import Version
from poetry.core.semver.version_range import VersionRange
from poetry.core.version.exceptions import InvalidVersion
from poetry.core.version.pep440 import ReleaseTag


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
            "1.0a1",
            "1.0a2.dev456",
            "1.0a12.dev456",
            "1.0a12",
            "1.0b1.dev456",
            "1.0b2",
            "1.0b2.post345.dev456",
            "1.0b2.post345",
            "1.0rc1.dev456",
            "1.0rc1",
            "1.0",
            "1.0+abc.5",
            "1.0+abc.7",
            "1.0+5",
            "1.0.post456.dev34",
            "1.0.post456",
            "1.1.dev1",
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
    assert not v.allows(Version.parse("2.2.3"))
    assert not v.allows(Version.parse("1.3.3"))
    assert not v.allows(Version.parse("1.2.4"))
    assert not v.allows(Version.parse("1.2.3-dev"))
    assert v.allows(Version.parse("1.2.3+build"))
    assert v.allows(Version.parse("1.2.3-1"))
    assert v.allows(Version.parse("1.2.3-1+build"))


def test_allows_with_local() -> None:
    v = Version.parse("1.2.3+build.1")
    assert v.allows(v)
    assert not v.allows(Version.parse("1.3.3"))
    assert not v.allows(Version.parse("1.2.3-dev"))
    assert not v.allows(Version.parse("1.2.3+build.2"))
    assert v.allows(Version.parse("1.2.3-1"))
    assert v.allows(Version.parse("1.2.3-1+build.1"))


def test_allows_with_post() -> None:
    v = Version.parse("1.2.3-1")
    assert v.allows(v)
    assert not v.allows(Version.parse("1.2.3"))
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


def test_allows_any() -> None:
    v = Version.parse("1.2.3")

    assert v.allows_any(v)
    assert not v.allows_any(Version.parse("0.0.3"))
    assert v.allows_any(VersionRange(Version.parse("1.1.4"), Version.parse("1.2.4")))
    assert v.allows_any(VersionRange())
    assert not v.allows_any(EmptyConstraint())


def test_intersect() -> None:
    v = Version.parse("1.2.3")

    assert v.intersect(v) == v
    assert v.intersect(Version.parse("1.1.4")).is_empty()
    assert (
        v.intersect(VersionRange(Version.parse("1.1.4"), Version.parse("1.2.4"))) == v
    )
    assert (
        Version.parse("1.1.4")
        .intersect(VersionRange(v, Version.parse("1.2.4")))
        .is_empty()
    )


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
    "version, expected",
    [
        ("1.2.3", "1.2.3-dev.0"),
        ("1.2.3-alpha.0", "1.2.3-alpha.0-dev.0"),
        ("1.2.3-dev.0", "1.2.3-dev.1"),
    ],
)
def test_next_devrelease(version: str, expected: str) -> None:
    v = Version.parse(version)
    assert v.next_devrelease() == Version.parse(expected)
