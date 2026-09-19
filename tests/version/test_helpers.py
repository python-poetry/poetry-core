from __future__ import annotations

import pytest

from poetry.core.constraints.version import parse_constraint
from poetry.core.version.helpers import PYTHON_VERSION
from poetry.core.version.helpers import format_python_constraint


@pytest.mark.parametrize(
    ("constraint", "expected"),
    [
        ("^3.10", ">=3.10,<4.0"),
        (">=3.16", ">=3.16"),
        ("~2.7 || ^3.6", ">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*"),
    ],
)
def test_format_python_constraint(constraint: str, expected: str) -> None:
    assert format_python_constraint(parse_constraint(constraint)) == expected


@pytest.mark.parametrize("constraint", ["4.0 || 4.1", "99.0 || 99.1"])
def test_format_python_constraint_union_outside_known_series(
    constraint: str,
) -> None:
    result = format_python_constraint(parse_constraint(constraint))

    assert "||" not in result
    assert result.startswith(">=")
    for version in PYTHON_VERSION:
        assert f"!={version}" in result
