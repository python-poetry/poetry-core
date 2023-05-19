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
