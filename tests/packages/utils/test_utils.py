import pytest

from poetry.core.packages.utils.utils import convert_markers
from poetry.core.packages.utils.utils import get_python_constraint_from_marker
from poetry.core.semver.helpers import parse_constraint
from poetry.core.version.markers import parse_marker


def test_convert_markers():
    marker = parse_marker(
        'sys_platform == "win32" and python_version < "3.6" '
        'or sys_platform == "win32" and python_version < "3.6" and python_version >= "3.3" '
        'or sys_platform == "win32" and python_version < "3.3"'
    )

    converted = convert_markers(marker)

    assert converted["python_version"] == [
        [("<", "3.6")],
        [("<", "3.6"), (">=", "3.3")],
        [("<", "3.3")],
    ]

    marker = parse_marker('python_version == "2.7" or python_version == "2.6"')
    converted = convert_markers(marker)

    assert converted["python_version"] == [[("==", "2.7")], [("==", "2.6")]]


@pytest.mark.parametrize(
    ["marker", "constraint"],
    [
        ('python_version >= "3.6" and python_full_version < "4.0"', ">=3.6, <4.0"),
        (
            'python_full_version >= "3.6.1" and python_full_version < "4.0.0"',
            ">=3.6.1, <4.0.0",
        ),
    ],
)
def test_get_python_constraint_from_marker(marker, constraint):
    marker = parse_marker(marker)
    constraint = parse_constraint(constraint)
    assert constraint == get_python_constraint_from_marker(marker)
