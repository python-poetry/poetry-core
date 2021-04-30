import pytest

from poetry.core.semver.helpers import parse_constraint
from poetry.core.semver.version import Version
from poetry.core.semver.version_range import VersionRange
from poetry.core.semver.version_union import VersionUnion
from poetry.core.version.pep440 import ReleaseTag


@pytest.mark.parametrize(
    "constraint,version",
    [
        (
            "~=3.8",
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(4, 0),
                include_min=True,
            ),
        ),
        (
            "== 3.8.*",
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(3, 9, 0),
                include_min=True,
            ),
        ),
        (
            "~= 3.8",
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(4, 0),
                include_min=True,
            ),
        ),
        (
            "~3.8",
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(3, 9),
                include_min=True,
            ),
        ),
        (
            "~ 3.8",
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(3, 9),
                include_min=True,
            ),
        ),
        (">3.8", VersionRange(min=Version.from_parts(3, 8))),
        (">=3.8", VersionRange(min=Version.from_parts(3, 8), include_min=True)),
        (">= 3.8", VersionRange(min=Version.from_parts(3, 8), include_min=True)),
        (
            ">3.8,<=6.5",
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(6, 5),
                include_max=True,
            ),
        ),
        (
            ">3.8,<= 6.5",
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(6, 5),
                include_max=True,
            ),
        ),
        (
            "> 3.8,<= 6.5",
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(6, 5),
                include_max=True,
            ),
        ),
        (
            "> 3.8,<=6.5",
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(6, 5),
                include_max=True,
            ),
        ),
        (
            ">3.8 ,<=6.5",
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(6, 5),
                include_max=True,
            ),
        ),
        (
            ">3.8, <=6.5",
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(6, 5),
                include_max=True,
            ),
        ),
        (
            ">3.8 , <=6.5",
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(6, 5),
                include_max=True,
            ),
        ),
        (
            "==3.8",
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(3, 8),
                include_min=True,
                include_max=True,
            ),
        ),
        (
            "== 3.8",
            VersionRange(
                min=Version.from_parts(3, 8),
                max=Version.from_parts(3, 8),
                include_min=True,
                include_max=True,
            ),
        ),
        (
            "~2.7 || ~3.8",
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
            "~2.7||~3.8",
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
            "~ 2.7||~ 3.8",
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
            "^1.0.0a1",
            VersionRange(
                min=Version.from_parts(1, 0, 0, pre=ReleaseTag("a", 1)),
                max=Version.from_parts(2, 0, 0),
                include_min=True,
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
    ],
)
def test_parse_constraint(constraint, version):
    assert parse_constraint(constraint) == version
