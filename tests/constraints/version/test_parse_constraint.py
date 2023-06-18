from __future__ import annotations

import pytest

from poetry.core.constraints.version import Version
from poetry.core.constraints.version import VersionConstraint
from poetry.core.constraints.version import VersionRange
from poetry.core.constraints.version import VersionUnion
from poetry.core.constraints.version import parse_constraint
from poetry.core.version.pep440 import ReleaseTag


@pytest.mark.parametrize(
    "input,constraint",
    [
        ("*", VersionRange()),
        ("*.*", VersionRange()),
        ("v*.*", VersionRange()),
        ("*.x.*", VersionRange()),
        ("x.X.x.*", VersionRange()),
        (">1.0.0", VersionRange(min=Version.from_parts(1, 0, 0))),
        ("<1.2.3", VersionRange(max=Version.from_parts(1, 2, 3))),
        ("<=1.2.3", VersionRange(max=Version.from_parts(1, 2, 3), include_max=True)),
        (">=1.2.3", VersionRange(min=Version.from_parts(1, 2, 3), include_min=True)),
        ("=1.2.3", Version.from_parts(1, 2, 3)),
        ("1.2.3", Version.from_parts(1, 2, 3)),
        ("1!2.3.4", Version.from_parts(2, 3, 4, epoch=1)),
        ("=1.0", Version.from_parts(1, 0, 0)),
        ("1.2.3b5", Version.from_parts(1, 2, 3, pre=ReleaseTag("beta", 5))),
        (
            "1.0.0a1.dev0",
            Version.from_parts(
                1, 0, 0, pre=ReleaseTag("a", 1), dev=ReleaseTag("dev", 0)
            ),
        ),
        (
            ">dev",
            VersionRange(min=Version.from_parts(0, 0, dev=ReleaseTag("dev"))),
        ),  # Issue 206
    ],
)
def test_parse_constraint(input: str, constraint: Version | VersionRange) -> None:
    assert parse_constraint(input) == constraint


@pytest.mark.parametrize(
    "input,constraint",
    [
        (
            "v2.*",
            VersionRange(Version.parse("2.dev0"), Version.parse("3.dev0"), True),
        ),
        (
            "2.*.*",
            VersionRange(Version.parse("2.dev0"), Version.parse("3.dev0"), True),
        ),
        (
            "20.*",
            VersionRange(Version.parse("20.dev0"), Version.parse("21.dev0"), True),
        ),
        (
            "20.*.*",
            VersionRange(Version.parse("20.dev0"), Version.parse("21.dev0"), True),
        ),
        (
            "2.0.*",
            VersionRange(Version.parse("2.0.dev0"), Version.parse("2.1.dev0"), True),
        ),
        (
            "2.x",
            VersionRange(Version.parse("2.dev0"), Version.parse("3.dev0"), True),
        ),
        (
            "2.x.x",
            VersionRange(Version.parse("2.dev0"), Version.parse("3.dev0"), True),
        ),
        (
            "2.2.X",
            VersionRange(Version.parse("2.2.dev0"), Version.parse("2.3.dev0"), True),
        ),
        ("0.*", VersionRange(Version.parse("0.dev0"), Version.parse("1.dev0"), True)),
        ("0.*.*", VersionRange(Version.parse("0.dev0"), Version.parse("1.dev0"), True)),
        ("0.x", VersionRange(Version.parse("0.dev0"), Version.parse("1.dev0"), True)),
        (
            "2.0.post1.*",
            VersionRange(
                min=Version.parse("2.0.post1.dev0"),
                max=Version.parse("2.0.post2.dev0"),
                include_min=True,
                include_max=False,
            ),
        ),
        (
            "2.0a1.*",
            VersionRange(
                min=Version.parse("2.0a1.dev0"),
                max=Version.parse("2.0a2.dev0"),
                include_min=True,
                include_max=False,
            ),
        ),
        (
            "2.0dev0.*",
            VersionRange(
                min=Version.parse("2.0dev0"),
                max=Version.parse("2.0dev1"),
                include_min=True,
                include_max=False,
            ),
        ),
    ],
)
def test_parse_constraint_wildcard(input: str, constraint: VersionRange) -> None:
    assert parse_constraint(input) == constraint


@pytest.mark.parametrize(
    "input,constraint",
    [
        (
            "~v1",
            VersionRange(
                Version.from_parts(1, 0, 0), Version.from_parts(2, 0, 0), True
            ),
        ),
        (
            "~1.0",
            VersionRange(
                Version.from_parts(1, 0, 0), Version.from_parts(1, 1, 0), True
            ),
        ),
        (
            "~1.0.0",
            VersionRange(
                Version.from_parts(1, 0, 0), Version.from_parts(1, 1, 0), True
            ),
        ),
        (
            "~1.2",
            VersionRange(
                Version.from_parts(1, 2, 0), Version.from_parts(1, 3, 0), True
            ),
        ),
        (
            "~1.2.3",
            VersionRange(
                Version.from_parts(1, 2, 3), Version.from_parts(1, 3, 0), True
            ),
        ),
        (
            "~1.0.0a1",
            VersionRange(
                min=Version.from_parts(1, 0, 0, pre=ReleaseTag("a", 1)),
                max=Version.from_parts(1, 1, 0),
                include_min=True,
            ),
        ),
        (
            "~1.0.0a1.dev0",
            VersionRange(
                min=Version.from_parts(
                    1, 0, 0, pre=ReleaseTag("a", 1), dev=ReleaseTag("dev", 0)
                ),
                max=Version.from_parts(1, 1, 0),
                include_min=True,
            ),
        ),
        (
            "~1.2-beta",
            VersionRange(
                Version.from_parts(1, 2, 0, pre=ReleaseTag("beta")),
                Version.from_parts(1, 3, 0),
                True,
            ),
        ),
        (
            "~1.2-b2",
            VersionRange(
                Version.from_parts(1, 2, 0, pre=ReleaseTag("beta", 2)),
                Version.from_parts(1, 3, 0),
                True,
            ),
        ),
        (
            "~0.3",
            VersionRange(
                Version.from_parts(0, 3, 0), Version.from_parts(0, 4, 0), True
            ),
        ),
        (
            "~3.5",
            VersionRange(
                Version.from_parts(3, 5, 0), Version.from_parts(3, 6, 0), True
            ),
        ),
        (
            "~=3.5",
            VersionRange(
                Version.from_parts(3, 5, 0), Version.from_parts(4, 0, 0), True
            ),
        ),  # PEP 440
        (
            "~=3.5.3",
            VersionRange(
                Version.from_parts(3, 5, 3), Version.from_parts(3, 6, 0), True
            ),
        ),  # PEP 440
        (
            "~=3.5.3rc1",
            VersionRange(
                Version.from_parts(3, 5, 3, pre=ReleaseTag("rc", 1)),
                Version.from_parts(3, 6, 0),
                True,
            ),
        ),  # PEP 440
    ],
)
def test_parse_constraint_tilde(input: str, constraint: VersionRange) -> None:
    assert parse_constraint(input) == constraint


@pytest.mark.parametrize(
    "input,constraint",
    [
        (
            "^v1",
            VersionRange(
                Version.from_parts(1, 0, 0), Version.from_parts(2, 0, 0), True
            ),
        ),
        ("^0", VersionRange(Version.from_parts(0), Version.from_parts(1), True)),
        (
            "^0.0",
            VersionRange(
                Version.from_parts(0, 0, 0), Version.from_parts(0, 1, 0), True
            ),
        ),
        (
            "^1.2",
            VersionRange(
                Version.from_parts(1, 2, 0), Version.from_parts(2, 0, 0), True
            ),
        ),
        (
            "^1.2.3-beta.2",
            VersionRange(
                Version.from_parts(1, 2, 3, pre=ReleaseTag("beta", 2)),
                Version.from_parts(2, 0, 0),
                True,
            ),
        ),
        (
            "^1.2.3",
            VersionRange(
                Version.from_parts(1, 2, 3), Version.from_parts(2, 0, 0), True
            ),
        ),
        (
            "^0.2.3",
            VersionRange(
                Version.from_parts(0, 2, 3), Version.from_parts(0, 3, 0), True
            ),
        ),
        (
            "^0.2",
            VersionRange(
                Version.from_parts(0, 2, 0), Version.from_parts(0, 3, 0), True
            ),
        ),
        (
            "^0.2.0",
            VersionRange(
                Version.from_parts(0, 2, 0), Version.from_parts(0, 3, 0), True
            ),
        ),
        (
            "^0.0.3",
            VersionRange(
                Version.from_parts(0, 0, 3), Version.from_parts(0, 0, 4), True
            ),
        ),
        (
            "^0.0.3-alpha.21",
            VersionRange(
                Version.from_parts(0, 0, 3, pre=ReleaseTag("alpha", 21)),
                Version.from_parts(0, 0, 4),
                True,
            ),
        ),
        (
            "^0.1.3-alpha.21",
            VersionRange(
                Version.from_parts(0, 1, 3, pre=ReleaseTag("alpha", 21)),
                Version.from_parts(0, 2, 0),
                True,
            ),
        ),
        (
            "^0.0.0-alpha.21",
            VersionRange(
                Version.from_parts(0, 0, 0, pre=ReleaseTag("alpha", 21)),
                Version.from_parts(0, 0, 1),
                True,
            ),
        ),
        (
            "^1.0.0a1",
            VersionRange(
                min=Version.from_parts(1, 0, 0, pre=ReleaseTag("a", 1)),
                max=Version.from_parts(2, 0, 0),
                include_min=True,
            ),
        ),
        (
            "^1.0.0a1.dev0",
            VersionRange(
                min=Version.from_parts(
                    1, 0, 0, pre=ReleaseTag("a", 1), dev=ReleaseTag("dev", 0)
                ),
                max=Version.from_parts(2, 0, 0),
                include_min=True,
            ),
        ),
    ],
)
def test_parse_constraint_caret(input: str, constraint: VersionRange) -> None:
    assert parse_constraint(input) == constraint


def test_parse_constraint_multi() -> None:
    assert parse_constraint(">2.0,<=3.0") == VersionRange(
        Version.from_parts(2, 0, 0),
        Version.from_parts(3, 0, 0),
        include_min=False,
        include_max=True,
    )


@pytest.mark.parametrize(
    "input, output",
    [
        (
            ">1!2,<=2!3",
            VersionRange(
                Version.from_parts(2, 0, 0, epoch=1),
                Version.from_parts(3, 0, 0, epoch=2),
                include_min=False,
                include_max=True,
            ),
        ),
        (
            ">=1!2,<2!3",
            VersionRange(
                Version.from_parts(2, 0, 0, epoch=1),
                Version.from_parts(3, 0, 0, epoch=2),
                include_min=True,
                include_max=False,
            ),
        ),
    ],
)
def test_parse_constraint_multi_with_epochs(input: str, output: VersionRange) -> None:
    assert parse_constraint(input) == output


def test_parse_constraint_multi_wildcard() -> None:
    assert parse_constraint(">=2.7,!=3.0.*,!=3.1.*") == VersionUnion(
        VersionRange(Version.parse("2.7"), Version.parse("3.0.dev0"), True, False),
        VersionRange(Version.parse("3.2.dev0"), None, True, False),
    )


@pytest.mark.parametrize(
    "input,constraint",
    [
        (
            "!=v2.*",
            VersionRange(max=Version.parse("2.0.0.dev0")).union(
                VersionRange(Version.parse("3.0.dev0"), include_min=True)
            ),
        ),
        (
            "!=2.*.*",
            VersionRange(max=Version.parse("2.0.0.dev0")).union(
                VersionRange(Version.parse("3.0.dev0"), include_min=True)
            ),
        ),
        (
            "!=2.0.*",
            VersionRange(max=Version.parse("2.0.0.dev0")).union(
                VersionRange(Version.parse("2.1.dev0"), include_min=True)
            ),
        ),
        (
            "!=0.*",
            VersionRange(max=Version.parse("0.dev0")).union(
                VersionRange(Version.parse("1.0.dev0"), include_min=True)
            ),
        ),
        (
            "!=0.*.*",
            VersionRange(max=Version.parse("0.dev0")).union(
                VersionRange(Version.parse("1.0.dev0"), include_min=True)
            ),
        ),
    ],
)
def test_parse_constraints_negative_wildcard(
    input: str, constraint: VersionRange
) -> None:
    assert parse_constraint(input) == constraint


@pytest.mark.parametrize(
    "input,constraint",
    [
        (">3.7,", VersionRange(min=Version.parse("3.7"))),
        (">3.7 , ", VersionRange(min=Version.parse("3.7"))),
        (
            ">3.7,<3.8,",
            VersionRange(min=Version.parse("3.7"), max=Version.parse("3.8")),
        ),
        (
            ">3.7,||<3.6,",
            VersionRange(min=Version.parse("3.7")).union(
                VersionRange(max=Version.parse("3.6"))
            ),
        ),
        (
            ">3.7 , || <3.6 , ",
            VersionRange(min=Version.parse("3.7")).union(
                VersionRange(max=Version.parse("3.6"))
            ),
        ),
        (
            ">3.7, <3.8, || <3.6, >3.5",
            VersionRange(min=Version.parse("3.7"), max=Version.parse("3.8")).union(
                VersionRange(min=Version.parse("3.5"), max=Version.parse("3.6"))
            ),
        ),
    ],
)
def test_parse_constraints_with_trailing_comma(
    input: str, constraint: VersionRange
) -> None:
    assert parse_constraint(input) == constraint


@pytest.mark.parametrize(
    "input, expected",
    [
        ("1", "1"),
        ("1.2", "1.2"),
        ("1.2.3", "1.2.3"),
        ("!=1", "!=1"),
        ("!=1.2", "!=1.2"),
        ("!=1.2.3", "!=1.2.3"),
        ("^1", ">=1,<2"),
        ("^1.0", ">=1.0,<2.0"),
        ("^1.0.0", ">=1.0.0,<2.0.0"),
        ("^1.0.0-alpha.1", ">=1.0.0-alpha.1,<2.0.0"),
        ("^0", ">=0,<1"),
        ("^0.1", ">=0.1,<0.2"),
        ("^0.0.2", ">=0.0.2,<0.0.3"),
        ("^0.1.2", ">=0.1.2,<0.2.0"),
        ("^0-alpha.1", ">=0-alpha.1,<1"),
        ("^0.1-alpha.1", ">=0.1-alpha.1,<0.2"),
        ("^0.0.2-alpha.1", ">=0.0.2-alpha.1,<0.0.3"),
        ("^0.1.2-alpha.1", ">=0.1.2-alpha.1,<0.2.0"),
        ("~1", ">=1,<2"),
        ("~1.0", ">=1.0,<1.1"),
        ("~1.0.0", ">=1.0.0,<1.1.0"),
    ],
)
def test_constraints_keep_version_precision(input: str, expected: str) -> None:
    assert str(parse_constraint(input)) == expected


@pytest.mark.parametrize(
    "constraint_parts,expected",
    [
        (["3.8"], Version.from_parts(3, 8)),
        (["=", "3.8"], Version.from_parts(3, 8)),
        (["==", "3.8"], Version.from_parts(3, 8)),
        ([">", "3.8"], VersionRange(min=Version.from_parts(3, 8))),
        ([">=", "3.8"], VersionRange(min=Version.from_parts(3, 8), include_min=True)),
        (["<", "3.8"], VersionRange(max=Version.from_parts(3, 8))),
        (["<=", "3.8"], VersionRange(max=Version.from_parts(3, 8), include_max=True)),
        (
            ["^", "3.8"],
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(4, 0),
                include_min=True,
            ),
        ),
        (
            ["~", "3.8"],
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(3, 9),
                include_min=True,
            ),
        ),
        (
            ["~=", "3.8"],
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(4, 0),
                include_min=True,
            ),
        ),
        (
            ["3.8.*"],
            VersionRange(
                min=Version.parse("3.8.0.dev0"),
                max=Version.parse("3.9.0.dev0"),
                include_min=True,
            ),
        ),
        (
            ["==", "3.8.*"],
            VersionRange(
                min=Version.parse("3.8.0.dev0"),
                max=Version.parse("3.9.0.dev0"),
                include_min=True,
            ),
        ),
        (
            ["!=", "3.8.*"],
            VersionRange(max=Version.parse("3.8.dev0")).union(
                VersionRange(Version.parse("3.9.dev0"), include_min=True)
            ),
        ),
        (
            [">", "3.8", ",", "<=", "6.5"],
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(6, 5),
                include_max=True,
            ),
        ),
        (
            [">=", "2.7", ",", "!=", "3.0.*", ",", "!=", "3.1.*"],
            VersionUnion(
                VersionRange(
                    Version.parse("2.7"), Version.parse("3.0.dev0"), True, False
                ),
                VersionRange(Version.parse("3.2.dev0"), None, True, False),
            ),
        ),
        (
            ["~", "2.7", "||", "~", "3.8"],
            VersionUnion(
                VersionRange(
                    min=Version.from_parts(2, 7),
                    max=Version.from_parts(2, 8),
                    include_min=True,
                ),
                VersionRange(
                    min=Version.from_parts(3, 8),
                    max=Version.from_parts(3, 9),
                    include_min=True,
                ),
            ),
        ),
        (
            ["~", "2.7", "||", "~", "3.8", "|", ">=", "3.10", ",", "<", "3.12"],
            VersionUnion(
                VersionRange(
                    min=Version.from_parts(2, 7),
                    max=Version.from_parts(2, 8),
                    include_min=True,
                ),
                VersionRange(
                    min=Version.from_parts(3, 8),
                    max=Version.from_parts(3, 9),
                    include_min=True,
                ),
                VersionRange(
                    min=Version.from_parts(3, 10),
                    max=Version.from_parts(3, 12),
                    include_min=True,
                ),
            ),
        ),
    ],
)
@pytest.mark.parametrize(("with_whitespace_padding",), [(True,), (False,)])
def test_parse_constraint_with_white_space_padding(
    constraint_parts: list[str],
    expected: VersionConstraint,
    with_whitespace_padding: bool,
) -> None:
    padding = " " * (4 if with_whitespace_padding else 0)
    constraint = padding.join(["", *constraint_parts, ""])
    assert parse_constraint(constraint) == expected
