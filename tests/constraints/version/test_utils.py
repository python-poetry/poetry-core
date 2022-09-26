from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from poetry.core.constraints.version import EmptyConstraint
from poetry.core.constraints.version import Version
from poetry.core.constraints.version import VersionRange
from poetry.core.constraints.version import constraint_regions


if TYPE_CHECKING:
    from poetry.core.constraints.version import VersionConstraint


PY27 = Version.parse("2.7")
PY30 = Version.parse("3")
PY36 = Version.parse("3.6.0")
PY37 = Version.parse("3.7")
PY38 = Version.parse("3.8.0")
PY40 = Version.parse("4.0.0")


@pytest.mark.parametrize(
    "versions, expected",
    [
        ([VersionRange(None, None)], [VersionRange(None, None)]),
        ([EmptyConstraint()], [VersionRange(None, None)]),
        (
            [VersionRange(PY27, None, include_min=True)],
            [
                VersionRange(None, PY27, include_max=False),
                VersionRange(PY27, None, include_min=True),
            ],
        ),
        (
            [VersionRange(None, PY40, include_max=False)],
            [
                VersionRange(None, PY40, include_max=False),
                VersionRange(PY40, None, include_min=True),
            ],
        ),
        (
            [VersionRange(PY27, PY27, include_min=True, include_max=True)],
            [
                VersionRange(None, PY27, include_max=False),
                VersionRange(PY27, PY27, include_min=True, include_max=True),
                VersionRange(PY27, None, include_min=False),
            ],
        ),
        (
            [VersionRange(PY27, PY30, include_min=True, include_max=False)],
            [
                VersionRange(None, PY27, include_max=False),
                VersionRange(PY27, PY30, include_min=True, include_max=False),
                VersionRange(PY30, None, include_min=True),
            ],
        ),
        (
            [
                VersionRange(PY27, PY30, include_min=True, include_max=False).union(
                    VersionRange(PY37, PY40, include_min=False, include_max=True)
                ),
                VersionRange(PY36, PY38, include_min=True, include_max=False),
            ],
            [
                VersionRange(None, PY27, include_max=False),
                VersionRange(PY27, PY30, include_min=True, include_max=False),
                VersionRange(PY30, PY36, include_min=True, include_max=False),
                VersionRange(PY36, PY37, include_min=True, include_max=True),
                VersionRange(PY37, PY38, include_min=False, include_max=False),
                VersionRange(PY38, PY40, include_min=True, include_max=True),
                VersionRange(PY40, None, include_min=False),
            ],
        ),
    ],
)
def test_constraint_regions(
    versions: list[VersionConstraint], expected: list[VersionRange]
) -> None:
    regions = constraint_regions(versions)
    assert regions == expected
