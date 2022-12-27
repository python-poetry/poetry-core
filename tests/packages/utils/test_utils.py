from __future__ import annotations

from pathlib import Path

import pytest

from poetry.core.constraints.generic import parse_constraint as parse_generic_constraint
from poetry.core.constraints.version import parse_constraint as parse_version_constraint
from poetry.core.packages.utils.utils import convert_markers
from poetry.core.packages.utils.utils import create_nested_marker
from poetry.core.packages.utils.utils import get_python_constraint_from_marker
from poetry.core.packages.utils.utils import is_python_project
from poetry.core.version.markers import parse_marker


@pytest.mark.parametrize(
    "marker, expected",
    [
        (
            (
                'sys_platform == "win32" and python_version < "3.6" or sys_platform =='
                ' "linux" and python_version < "3.6" and python_version >= "3.3" or'
                ' sys_platform == "darwin" and python_version < "3.3"'
            ),
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
            (
                'sys_platform == "win32" and python_version < "3.6" or sys_platform =='
                ' "win32" and python_version < "3.6" and python_version >= "3.3" or'
                ' sys_platform == "win32" and python_version < "3.3"'
            ),
            {"python_version": [[("<", "3.6")]], "sys_platform": [[("==", "win32")]]},
        ),
        (
            'python_version == "2.7" or python_version == "2.6"',
            {"python_version": [[("==", "2.7")], [("==", "2.6")]]},
        ),
        (
            (
                '(python_version < "2.7" or python_full_version >= "3.0.0") and'
                ' python_full_version < "3.6.0"'
            ),
            {"python_version": [[("<", "2.7")], [(">=", "3.0.0"), ("<", "3.6.0")]]},
        ),
        (
            (
                '(python_version < "2.7" or python_full_version >= "3.0.0") and'
                ' extra == "foo"'
            ),
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
    ["constraint", "expected"],
    [
        ("*", ""),
        ("==linux", 'sys_platform == "linux"'),
        ("!=win32", 'sys_platform != "win32"'),
        ("!=linux, !=win32", 'sys_platform != "linux" and sys_platform != "win32"'),
        ("==linux || ==win32", 'sys_platform == "linux" or sys_platform == "win32"'),
    ],
)
def test_create_nested_marker_base_constraint(constraint: str, expected: str) -> None:
    assert (
        create_nested_marker("sys_platform", parse_generic_constraint(constraint))
        == expected
    )


@pytest.mark.parametrize(
    ["constraint", "expected"],
    [
        ("*", ""),
        # simple version
        ("3", 'python_version == "3"'),
        ("3.9", 'python_version == "3.9"'),
        ("3.9.0", 'python_full_version == "3.9.0"'),
        ("3.9.1", 'python_full_version == "3.9.1"'),
        # min
        (">=3", 'python_version >= "3"'),
        (">=3.9", 'python_version >= "3.9"'),
        (">=3.9.0", 'python_full_version >= "3.9.0"'),
        (">=3.9.1", 'python_full_version >= "3.9.1"'),
        (">3", 'python_full_version > "3.0.0"'),
        (">3.9", 'python_full_version > "3.9.0"'),
        (">3.9.0", 'python_full_version > "3.9.0"'),
        (">3.9.1", 'python_full_version > "3.9.1"'),
        # max
        ("<3", 'python_version < "3"'),
        ("<3.9", 'python_version < "3.9"'),
        ("<3.9.0", 'python_full_version < "3.9.0"'),
        ("<3.9.1", 'python_full_version < "3.9.1"'),
        ("<=3", 'python_full_version <= "3.0.0"'),
        ("<=3.9", 'python_full_version <= "3.9.0"'),
        ("<=3.9.0", 'python_full_version <= "3.9.0"'),
        ("<=3.9.1", 'python_full_version <= "3.9.1"'),
        # min and max
        (">=3.7, <3.9", 'python_version >= "3.7" and python_version < "3.9"'),
        (">=3.7, <=3.9", 'python_version >= "3.7" and python_full_version <= "3.9.0"'),
        (">3.7, <3.9", 'python_full_version > "3.7.0" and python_version < "3.9"'),
        (
            ">3.7, <=3.9",
            'python_full_version > "3.7.0" and python_full_version <= "3.9.0"',
        ),
        # union
        ("<3.7 || >=3.8", '(python_version < "3.7") or (python_version >= "3.8")'),
        (
            ">=3.7,<3.8 || >=3.9,<=3.10",
            (
                '(python_version >= "3.7" and python_version < "3.8")'
                ' or (python_version >= "3.9" and python_full_version <= "3.10.0")'
            ),
        ),
    ],
)
def test_create_nested_marker_version_constraint(
    constraint: str,
    expected: str,
) -> None:
    assert (
        create_nested_marker("python_version", parse_version_constraint(constraint))
        == expected
    )


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
        ('python_version <= "3"', "<3"),
        ('python_version > "3"', ">=3"),
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
            (
                'python_version >= "3.7" and python_version < "3.8" or python_version'
                ' >= "3.9" and python_version < "3.10"'
            ),
            ">=3.7,<3.8 || >=3.9,<3.10",
        ),
        (
            (
                '(python_version < "2.7" or python_full_version >= "3.0.0") and'
                ' python_full_version < "3.6.0"'
            ),
            "<2.7 || >=3.0,<3.6",
        ),
        # no python_version
        ('sys_platform == "linux"', "*"),
        ('sys_platform != "linux" and sys_platform != "win32"', "*"),
        ('sys_platform == "linux" or sys_platform == "win32"', "*"),
        # no relevant python_version
        ('python_version >= "3.9" or sys_platform == "linux"', "*"),
        # relevant python_version
        ('python_version >= "3.9" and sys_platform == "linux"', ">=3.9"),
        # exclude specific version
        (
            'python_version >= "3.5" and python_full_version != "3.7.6"',
            ">=3.5,<3.7.6 || >3.7.6",
        ),
        # Full exact version
        (
            'python_full_version == "3.6.1"',
            "3.6.1",
        ),
    ],
)
def test_get_python_constraint_from_marker(marker: str, constraint: str) -> None:
    marker_parsed = parse_marker(marker)
    constraint_parsed = parse_version_constraint(constraint)
    assert get_python_constraint_from_marker(marker_parsed) == constraint_parsed


@pytest.mark.parametrize(
    ("fixture", "result"),
    [
        ("simple_project", True),
        ("project_with_setup_cfg_only", True),
        ("project_with_setup", True),
        ("project_with_pep517_non_poetry", True),
        ("project_without_pep517", False),
        ("does_not_exist", False),
    ],
)
def test_is_python_project(fixture: str, result: bool) -> None:
    path = Path(__file__).parent.parent.parent / "fixtures" / fixture
    assert is_python_project(path) == result
