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
            {
                "python_version": [
                    [("<", "3.6")],
                    [("<", "3.6"), (">=", "3.3")],
                    [("<", "3.3")],
                ],
                "sys_platform": [
                    [("==", "win32")],
                    [("==", "linux")],
                    [("==", "darwin")],
                ],
            },
        ),
        (
            'sys_platform == "win32" and python_version < "3.6" or sys_platform =='
            ' "win32" and python_version < "3.6" and python_version >= "3.3" or'
            ' sys_platform == "win32" and python_version < "3.3"',
            {"python_version": [[("<", "3.6")]], "sys_platform": [[("==", "win32")]]},
        ),
        (
            'python_version == "2.7" or python_version == "2.6"',
            {"python_version": [[("==", "2.7")], [("==", "2.6")]]},
        ),
        (
            '(python_version < "2.7" or python_full_version >= "3.0.0") and'
            ' python_full_version < "3.6.0"',
            {"python_version": [[("<", "2.7")], [(">=", "3.0.0"), ("<", "3.6.0")]]},
        ),
        (
            '(python_version < "2.7" or python_full_version >= "3.0.0") and'
            ' extra == "foo"',
            {
                "extra": [[("==", "foo")]],
                "python_version": [[("<", "2.7")], [(">=", "3.0.0")]],
            },
        ),
        (
            'python_version >= "3.9" or sys_platform == "linux"',
            {
                "python_version": [[(">=", "3.9")], []],
                "sys_platform": [[], [("==", "linux")]],
            },
        ),
        (
            'python_version >= "3.9" and sys_platform == "linux"',
            {
                "python_version": [[(">=", "3.9")]],
                "sys_platform": [[("==", "linux")]],
            },
        ),
    ],
)
def test_convert_markers(
    marker: str, expected: dict[str, list[list[tuple[str, str]]]]
) -> None:
    parsed_marker = parse_marker(marker)
    converted = convert_markers(parsed_marker)
    assert converted == expected


@pytest.mark.parametrize(
    ["marker", "constraint"],
    [
        # ==
        ('python_version == "3.6"', "~3.6"),
        ('python_version == "3.6.*"', "==3.6.*"),
        ('python_version == "3.6.* "', "==3.6.*"),
        # !=
        ('python_version != "3.6"', "!=3.6.*"),
        ('python_version != "3.6.*"', "!=3.6.*"),
        ('python_version != "3.6.* "', "!=3.6.*"),
        # <, <=, >, >= precision 1
        ('python_version < "3"', "<3"),
        ('python_version <= "3"', "<4"),
        ('python_version > "3"', ">=4"),
        ('python_version >= "3"', ">=3"),
        # <, <=, >, >= precision 2
        ('python_version < "3.6"', "<3.6"),
        ('python_version <= "3.6"', "<3.7"),
        ('python_version > "3.6"', ">=3.7"),
        ('python_version >= "3.6"', ">=3.6"),
        # in, not in
        ('python_version in "2.7, 3.6"', ">=2.7.0,<2.8.0 || >=3.6.0,<3.7.0"),
        ('python_version in "2.7, 3.6.2"', ">=2.7.0,<2.8.0 || 3.6.2"),
        ('python_version not in "2.7, 3.6"', "<2.7.0 || >=2.8.0,<3.6.0 || >=3.7.0"),
        ('python_version not in "2.7, 3.6.2"', "<2.7.0 || >=2.8.0,<3.6.2 || >3.6.2"),
        # and
        ('python_version >= "3.6" and python_full_version < "4.0"', ">=3.6, <4.0"),
        (
            'python_full_version >= "3.6.1" and python_full_version < "4.0.0"',
            ">=3.6.1, <4.0.0",
        ),
        # or
        ('python_version < "3.6" or python_version >= "3.9"', "<3.6 || >=3.9"),
        # and or
        (
            'python_version >= "3.7" and python_version < "3.8" or python_version >='
            ' "3.9" and python_version < "3.10"',
            ">=3.7,<3.8 || >=3.9,<3.10",
        ),
        (
            '(python_version < "2.7" or python_full_version >= "3.0.0") and'
            ' python_full_version < "3.6.0"',
            "<2.7 || >=3.0,<3.6",
        ),
        # no python_version
        ('sys_platform == "linux"', "*"),
        # no relevant python_version
        ('python_version >= "3.9" or sys_platform == "linux"', "*"),
        # relevant python_version
        ('python_version >= "3.9" and sys_platform == "linux"', ">=3.9"),
    ],
)
def test_get_python_constraint_from_marker(marker: str, constraint: str) -> None:
    marker_parsed = parse_marker(marker)
    constraint_parsed = parse_constraint(constraint)
    assert get_python_constraint_from_marker(marker_parsed) == constraint_parsed
