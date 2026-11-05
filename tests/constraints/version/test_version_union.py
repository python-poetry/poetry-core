from __future__ import annotations

import pytest

from poetry.core.constraints.version import Version
from poetry.core.constraints.version import VersionRange
from poetry.core.constraints.version import VersionUnion
from poetry.core.constraints.version import parse_constraint


@pytest.mark.parametrize(
    ("ranges", "expected"),
    [
        (  # positive
            [
                VersionRange(max=Version.parse("1.2")),
                VersionRange(Version.parse("1.3.dev0"), include_min=True),
            ],
            True,
        ),
        (  # positive inverted order
            [
                VersionRange(Version.parse("1.3.dev0"), include_min=True),
                VersionRange(max=Version.parse("1.2")),
            ],
            True,
        ),
        (  # too many ranges
            [
                VersionRange(max=Version.parse("1.2")),
                VersionRange(Version.parse("1.3"), include_min=True),
                VersionRange(max=Version.parse("1.4")),
            ],
            False,
        ),
        ([VersionRange(max=Version.parse("1.2"))], False),  # too little ranges
        (  # additional include_max
            [
                VersionRange(max=Version.parse("1.2"), include_max=True),
                VersionRange(Version.parse("1.3"), include_min=True),
            ],
            False,
        ),
        (  # missing include_min
            [
                VersionRange(max=Version.parse("1.2")),
                VersionRange(Version.parse("1.3")),
            ],
            False,
        ),
        (  # additional min
            [
                VersionRange(Version.parse("1.0"), Version.parse("1.2")),
                VersionRange(Version.parse("1.3"), include_min=True),
            ],
            False,
        ),
        (  # additional max
            [
                VersionRange(max=Version.parse("1.2")),
                VersionRange(
                    Version.parse("1.3"), Version.parse("1.4"), include_min=True
                ),
            ],
            False,
        ),
        (  # missing max
            [
                VersionRange(),
                VersionRange(Version.parse("1.3"), include_min=True),
            ],
            False,
        ),
        (  # missing min
            [
                VersionRange(max=Version.parse("1.2")),
                VersionRange(include_min=True),
            ],
            False,
        ),
    ],
)
def test_excludes_single_wildcard_range_basics(
    ranges: list[VersionRange], expected: bool
) -> None:
    assert VersionUnion(*ranges).excludes_single_wildcard_range is expected


@pytest.mark.parametrize(
    ("max", "min", "expected"),
    [
        # simple exclude wildcard range
        ("1.2", "1.3.dev0", True),
        ("1.2.dev0", "1.3.dev0", True),
        ("1", "2.dev0", True),
        ("1.2.3.4.5", "1.2.3.4.6.dev0", True),
        # simple non exclude wildcard range
        ("1.2", "1.3", False),
        ("1.2", "1.3a0.dev0", False),
        ("1.2", "1.3.post0.dev0", False),
        ("1.2", "1.3.dev0+local", False),
        ("1.2", "1.3.dev1", False),
        ("1.2.post0", "1.3.dev0", False),
        ("1.2a0", "1.3.dev0", False),
        ("1.2+local", "1.3.dev0", False),
        ("1.2.dev1", "1.3.dev0", False),
        # more complicated cases
        ("1", "1.0.0.1.dev0", True),
        ("1.2.0.0", "1.3.dev0", True),
        ("1.2.0.0.dev0", "1.3.dev0", True),
        ("1.2", "1.3.0.dev0", True),
        ("1.2.0.0", "1.3.1.dev0", False),
        ("1.2", "1.4.dev0", False),
        ("1.2", "2.3.dev0", False),
        # post releases
        ("2.0.post1", "2.0.post2.dev0", True),
        ("2.0.post1.dev0", "2.0.post2.dev0", True),
        ("2.0.post1.dev1", "2.0.post2.dev0", False),
        ("2.0.post1", "2.0.post2.dev1", False),
        ("2.0.post0", "2.0.post2.dev0", False),
        ("2.0.post1", "2.0.post1.dev0", False),
    ],
)
def test_excludes_single_wildcard_range(max: str, min: str, expected: bool) -> None:
    version_union = VersionUnion(
        VersionRange(max=Version.parse(max)),
        VersionRange(Version.parse(min), include_min=True),
    )
    assert version_union.excludes_single_wildcard_range is expected


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        # simple unions
        ("<1 || >=2", "<1 || >=2"),
        ("<1.2 || >=2.3.dev0", "<1.2 || >=2.3.dev0"),
        # version exclusions
        ("!=1.0", "!=1.0"),
        ("!=1.0+local", "!=1.0+local"),
        # punctured ranges round-trip through string serialization
        (">1,!=2", ">1,!=2"),
        (">=1,!=2,<5", ">=1,!=2,<5"),
        (">=1,!=2,!=3,<5", ">=1,!=2,!=3,<5"),
        # canonical (PEP 440 ordered) `<V || >V` is *not* `!=V` -- it
        # excludes V's prereleases too -- so it must NOT collapse
        ("<2 || >2", "<2 || >2"),
        # wildcard exclusions
        ("!=1.*", "!=1.*"),
        ("!=1.0.*", "!=1.0.*"),
        ("!=1.2.*", "!=1.2.*"),
        ("!=1.2.3.4.5.*", "!=1.2.3.4.5.*"),
        ("!=2.0.post1.*", "!=2.0.post1.*"),
        ("!=2.1.post0.*", "!=2.1.post0.*"),
        ("<1 || >=2.dev0", "!=1.*"),
    ],
)
def test_str(version: str, expected: str) -> None:
    assert str(parse_constraint(version)) == expected


@pytest.mark.parametrize(
    ("constraint", "version", "expected"),
    [
        # post-releases of the excluded version must still be allowed
        (">0.9,!=1.0", "1.post1", True),
        (">0.9,!=1.0", "1.post1+local", True),
        (">=2,!=3.0,<4", "3.post1", True),
        (">=1,!=2,!=3,<4", "2.post1", True),
        (">=1,!=2,!=3,<4", "3.post2", True),
        ("!=2,<=3.3", "2.post3.dev1", True),
        # post-releases of a pre-release seam
        (">0.5,!=1.0a1", "1.0a1.post1", True),
        # the excluded point itself and its local variants stay excluded
        (">0.9,!=1.0", "1.0", False),
        (">0.9,!=1.0", "1.0+local", False),
        (">0.9,!=1.0", "1.0.0", False),
        (">=2,!=3.0,<4", "3.0", False),
        # pre/dev variants of the excluded version are still allowed
        (">0.9,!=1.0", "1.0.dev1", True),
        (">0.9,!=1.0", "1.0a1", True),
        # the outer bounds still apply
        (">0.9,!=1.0", "0.9", False),
        (">0.9,!=1.0", "0.95", True),
        (">=2,!=3.0,<4", "4.0", False),
        (">=2,!=3.0,<4", "1.9", False),
        # post-releases of a lower bound are still rejected (PEP 440)
        (">0,!=0.4.2,<4.3", "0.post3", False),
        (">0,!=3.2", "0.post3", False),
        # other post-releases near a post-release seam are unaffected
        (">3,!=3.post2", "3.post0", False),
        (">3,!=3.post2", "3.post2", False),
        (">3,!=3.post2", "3.post3", True),
        # a literal exclusive comparison still rejects post-releases
        (">1.0", "1.post1", False),
        ("<1.0 || >2.0", "2.post1", False),
    ],
)
def test_allows_punctured_union_post_releases(
    constraint: str, version: str, expected: bool
) -> None:
    assert parse_constraint(constraint).allows(Version.parse(version)) is expected


@pytest.mark.parametrize(
    ("constraint", "version"),
    [
        (">0.9,!=1.0", "1.post1"),
        (">=2,!=3.0,<4", "3.post1"),
        (">=1,!=2,!=3,<4", "2.post1"),
    ],
)
def test_punctured_union_set_operations_with_allowed_point(
    constraint: str, version: str
) -> None:
    u = parse_constraint(constraint)
    point = Version.parse(version)

    assert u.intersect(point) == point
    assert u.allows_any(point)
    assert u.allows_all(point)

    difference = u.difference(point)
    assert not difference.allows(point)
    assert difference.allows(Version.parse("0.95" if "0.9" in constraint else "2.5"))


@pytest.mark.parametrize(
    ("constraint", "version"),
    [
        (">0.9,!=1.0", "1.0"),
        (">0.9,!=1.0", "1.0+local"),
    ],
)
def test_punctured_union_set_operations_with_excluded_point(
    constraint: str, version: str
) -> None:
    u = parse_constraint(constraint)
    point = Version.parse(version)

    assert u.intersect(point).is_empty()
    assert not u.allows_any(point)
