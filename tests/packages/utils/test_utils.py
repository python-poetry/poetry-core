from __future__ import annotations

import pytest

from poetry.core.packages.utils.utils import convert_markers
from poetry.core.packages.utils.utils import get_python_constraint_from_marker
from poetry.core.semver.helpers import parse_constraint
from poetry.core.version.markers import parse_marker


@pytest.mark.parametrize(
    "marker, expected",
    [
        (
            'sys_platform == "win32" and python_version < "3.6" or sys_platform =='
            ' "linux" and python_version < "3.6" and python_version >= "3.3" or'
            ' sys_platform == "darwin" and python_version < "3.3"',
            [
                [("<", "3.6")],
                [("<", "3.6"), (">=", "3.3")],
                [("<", "3.3")],
            ],
        ),
        (
            'sys_platform == "win32" and python_version < "3.6" or sys_platform =='
            ' "win32" and python_version < "3.6" and python_version >= "3.3" or'
            ' sys_platform == "win32" and python_version < "3.3"',
            [[("<", "3.6")]],
        ),
        (
            'python_version == "2.7" or python_version == "2.6"',
            [[("==", "2.7")], [("==", "2.6")]],
        ),
    ],
)
def test_convert_markers(marker: str, expected: list[list[tuple[str, str]]]) -> None:
    parsed_marker = parse_marker(marker)
    converted = convert_markers(parsed_marker)
    assert converted["python_version"] == expected


@pytest.mark.parametrize(
    ["marker", "constraint"],
    [
        ('python_version >= "3.6" and python_full_version < "4.0"', ">=3.6, <4.0"),
        (
            'python_full_version >= "3.6.1" and python_full_version < "4.0.0"',
            ">=3.6.1, <4.0.0",
        ),
        ('sys_platform == "linux"', "*"),
    ],
)
def test_get_python_constraint_from_marker(marker: str, constraint: str) -> None:
    marker_parsed = parse_marker(marker)
    constraint_parsed = parse_constraint(constraint)
    assert constraint_parsed == get_python_constraint_from_marker(marker_parsed)
