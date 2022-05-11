from __future__ import annotations

import os

from typing import TYPE_CHECKING

import pytest

from poetry.core.version.markers import AnyMarker
from poetry.core.version.markers import EmptyMarker
from poetry.core.version.markers import MarkerUnion
from poetry.core.version.markers import MultiMarker
from poetry.core.version.markers import SingleMarker
from poetry.core.version.markers import dnf
from poetry.core.version.markers import parse_marker


if TYPE_CHECKING:
    from poetry.core.version.markers import BaseMarker


def test_single_marker() -> None:
    m = parse_marker('sys_platform == "darwin"')

    assert isinstance(m, SingleMarker)
    assert m.name == "sys_platform"
    assert m.constraint_string == "==darwin"

    m = parse_marker('python_version in "2.7, 3.0, 3.1"')

    assert isinstance(m, SingleMarker)
    assert m.name == "python_version"
    assert m.constraint_string == "in 2.7, 3.0, 3.1"
    assert str(m.constraint) == ">=2.7.0,<2.8.0 || >=3.0.0,<3.2.0"

    m = parse_marker('"2.7" in python_version')

    assert isinstance(m, SingleMarker)
    assert m.name == "python_version"
    assert m.constraint_string == "in 2.7"
    assert str(m.constraint) == ">=2.7.0,<2.8.0"

    m = parse_marker('python_version not in "2.7, 3.0, 3.1"')

    assert isinstance(m, SingleMarker)
    assert m.name == "python_version"
    assert m.constraint_string == "not in 2.7, 3.0, 3.1"
    assert str(m.constraint) == "<2.7.0 || >=2.8.0,<3.0.0 || >=3.2.0"

    m = parse_marker(
        "platform_machine in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE amd64 AMD64"
        " win32 WIN32'"
    )

    assert isinstance(m, SingleMarker)
    assert m.name == "platform_machine"
    assert (
        m.constraint_string
        == "in x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE amd64 AMD64 win32 WIN32"
    )
    assert (
        str(m.constraint)
        == "x86_64 || X86_64 || aarch64 || AARCH64 || ppc64le || PPC64LE || amd64 ||"
        " AMD64 || win32 || WIN32"
    )

    m = parse_marker(
        "platform_machine not in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE amd64"
        " AMD64 win32 WIN32'"
    )

    assert isinstance(m, SingleMarker)
    assert m.name == "platform_machine"
    assert (
        m.constraint_string
        == "not in x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE amd64 AMD64 win32"
        " WIN32"
    )
    assert (
        str(m.constraint)
        == "!=x86_64, !=X86_64, !=aarch64, !=AARCH64, !=ppc64le, !=PPC64LE, !=amd64,"
        " !=AMD64, !=win32, !=WIN32"
    )


def test_single_marker_intersect() -> None:
    m = parse_marker('sys_platform == "darwin"')

    intersection = m.intersect(parse_marker('implementation_name == "cpython"'))
    assert (
        str(intersection)
        == 'sys_platform == "darwin" and implementation_name == "cpython"'
    )

    m = parse_marker('python_version >= "3.4"')

    intersection = m.intersect(parse_marker('python_version < "3.6"'))
    assert str(intersection) == 'python_version >= "3.4" and python_version < "3.6"'


def test_single_marker_intersect_compacts_constraints() -> None:
    m = parse_marker('python_version < "3.6"')

    intersection = m.intersect(parse_marker('python_version < "3.4"'))
    assert str(intersection) == 'python_version < "3.4"'


def test_single_marker_intersect_with_multi() -> None:
    m = parse_marker('sys_platform == "darwin"')

    intersection = m.intersect(
        parse_marker('implementation_name == "cpython" and python_version >= "3.6"')
    )
    assert (
        str(intersection)
        == 'implementation_name == "cpython" and python_version >= "3.6" and'
        ' sys_platform == "darwin"'
    )


def test_single_marker_intersect_with_multi_with_duplicate() -> None:
    m = parse_marker('python_version < "4.0"')

    intersection = m.intersect(
        parse_marker('sys_platform == "darwin" and python_version < "4.0"')
    )
    assert str(intersection) == 'sys_platform == "darwin" and python_version < "4.0"'


def test_single_marker_intersect_with_multi_compacts_constraint() -> None:
    m = parse_marker('python_version < "3.6"')

    intersection = m.intersect(
        parse_marker('implementation_name == "cpython" and python_version < "3.4"')
    )
    assert (
        str(intersection)
        == 'implementation_name == "cpython" and python_version < "3.4"'
    )


def test_single_marker_intersect_with_union_leads_to_single_marker() -> None:
    m = parse_marker('python_version >= "3.6"')

    intersection = m.intersect(
        parse_marker('python_version < "3.6" or python_version >= "3.7"')
    )
    assert str(intersection) == 'python_version >= "3.7"'


def test_single_marker_intersect_with_union_leads_to_empty() -> None:
    m = parse_marker('python_version == "3.7"')

    intersection = m.intersect(
        parse_marker('python_version < "3.7" or python_version >= "3.8"')
    )
    assert intersection.is_empty()


def test_single_marker_not_in_python_intersection() -> None:
    m = parse_marker('python_version not in "2.7, 3.0, 3.1"')

    intersection = m.intersect(
        parse_marker('python_version not in "2.7, 3.0, 3.1, 3.2"')
    )
    assert str(intersection) == 'python_version not in "2.7, 3.0, 3.1, 3.2"'


def test_marker_intersection_of_python_version_and_python_full_version() -> None:
    m = parse_marker('python_version >= "3.6"')
    m2 = parse_marker('python_full_version >= "3.0.0"')
    intersection = m.intersect(m2)

    assert str(intersection) == 'python_version >= "3.6"'


def test_single_marker_union() -> None:
    m = parse_marker('sys_platform == "darwin"')

    union = m.union(parse_marker('implementation_name == "cpython"'))
    assert str(union) == 'sys_platform == "darwin" or implementation_name == "cpython"'


def test_single_marker_union_is_any() -> None:
    m = parse_marker('python_version >= "3.4"')

    union = m.union(parse_marker('python_version < "3.6"'))
    assert union.is_any()


@pytest.mark.parametrize(
    ("marker1", "marker2", "expected"),
    [
        (
            'python_version < "3.6"',
            'python_version < "3.4"',
            'python_version < "3.6"',
        ),
        (
            'sys_platform == "linux"',
            'sys_platform != "win32"',
            'sys_platform != "win32"',
        ),
        (
            'python_version == "3.6"',
            'python_version > "3.6"',
            'python_version >= "3.6"',
        ),
        (
            'python_version == "3.6"',
            'python_version < "3.6"',
            'python_version <= "3.6"',
        ),
        (
            'python_version < "3.6"',
            'python_version > "3.6"',
            'python_version != "3.6"',
        ),
    ],
)
def test_single_marker_union_is_single_marker(
    marker1: str, marker2: str, expected: str
) -> None:
    m = parse_marker(marker1)

    union = m.union(parse_marker(marker2))
    assert str(union) == expected


def test_single_marker_union_with_multi() -> None:
    m = parse_marker('sys_platform == "darwin"')

    union = m.union(
        parse_marker('implementation_name == "cpython" and python_version >= "3.6"')
    )
    assert (
        str(union)
        == 'implementation_name == "cpython" and python_version >= "3.6" or'
        ' sys_platform == "darwin"'
    )


def test_single_marker_union_with_multi_duplicate() -> None:
    m = parse_marker('sys_platform == "darwin" and python_version >= "3.6"')

    union = m.union(
        parse_marker('sys_platform == "darwin" and python_version >= "3.6"')
    )
    assert str(union) == 'sys_platform == "darwin" and python_version >= "3.6"'


@pytest.mark.parametrize(
    ("single_marker", "multi_marker", "expected"),
    [
        (
            'python_version >= "3.6"',
            'python_version >= "3.7" and sys_platform == "win32"',
            'python_version >= "3.6"',
        ),
        (
            'sys_platform == "linux"',
            'sys_platform != "linux" and sys_platform != "win32"',
            'sys_platform != "win32"',
        ),
    ],
)
def test_single_marker_union_with_multi_is_single_marker(
    single_marker: str, multi_marker: str, expected: str
) -> None:
    m = parse_marker(single_marker)
    union = m.union(parse_marker(multi_marker))
    assert str(union) == expected


def test_single_marker_union_with_multi_cannot_be_simplified() -> None:
    m = parse_marker('python_version >= "3.7"')
    union = m.union(parse_marker('python_version >= "3.6" and sys_platform == "win32"'))
    assert (
        str(union)
        == 'python_version >= "3.6" and sys_platform == "win32" or python_version >='
        ' "3.7"'
    )


def test_single_marker_union_with_multi_is_union_of_single_markers() -> None:
    m = parse_marker('python_version >= "3.6"')
    union = m.union(parse_marker('python_version < "3.6" and sys_platform == "win32"'))
    assert str(union) == 'sys_platform == "win32" or python_version >= "3.6"'


def test_single_marker_union_with_multi_union_is_union_of_single_markers() -> None:
    m = parse_marker('python_version >= "3.6"')
    union = m.union(
        parse_marker(
            'python_version < "3.6" and sys_platform == "win32" or python_version <'
            ' "3.6" and sys_platform == "linux"'
        )
    )
    assert (
        str(union)
        == 'sys_platform == "win32" or sys_platform == "linux" or python_version >='
        ' "3.6"'
    )


def test_single_marker_union_with_union() -> None:
    m = parse_marker('sys_platform == "darwin"')

    union = m.union(
        parse_marker('implementation_name == "cpython" or python_version >= "3.6"')
    )
    assert (
        str(union)
        == 'implementation_name == "cpython" or python_version >= "3.6" or sys_platform'
        ' == "darwin"'
    )


def test_single_marker_not_in_python_union() -> None:
    m = parse_marker('python_version not in "2.7, 3.0, 3.1"')

    union = m.union(parse_marker('python_version not in "2.7, 3.0, 3.1, 3.2"'))
    assert str(union) == 'python_version not in "2.7, 3.0, 3.1"'


def test_single_marker_union_with_union_duplicate() -> None:
    m = parse_marker('sys_platform == "darwin"')

    union = m.union(parse_marker('sys_platform == "darwin" or python_version >= "3.6"'))
    assert str(union) == 'sys_platform == "darwin" or python_version >= "3.6"'

    m = parse_marker('python_version >= "3.7"')

    union = m.union(parse_marker('sys_platform == "darwin" or python_version >= "3.6"'))
    assert str(union) == 'sys_platform == "darwin" or python_version >= "3.6"'

    m = parse_marker('python_version <= "3.6"')

    union = m.union(parse_marker('sys_platform == "darwin" or python_version < "3.4"'))
    assert str(union) == 'sys_platform == "darwin" or python_version <= "3.6"'


def test_single_marker_union_with_inverse() -> None:
    m = parse_marker('sys_platform == "darwin"')
    union = m.union(parse_marker('sys_platform != "darwin"'))
    assert union.is_any()


def test_multi_marker() -> None:
    m = parse_marker('sys_platform == "darwin" and implementation_name == "cpython"')

    assert isinstance(m, MultiMarker)
    assert m.markers == [
        parse_marker('sys_platform == "darwin"'),
        parse_marker('implementation_name == "cpython"'),
    ]


def test_multi_marker_is_empty_is_contradictory() -> None:
    m = parse_marker(
        'sys_platform == "linux" and python_version >= "3.5" and python_version < "2.8"'
    )

    assert m.is_empty()

    m = parse_marker('sys_platform == "linux" and sys_platform == "win32"')

    assert m.is_empty()


def test_multi_marker_intersect_multi() -> None:
    m = parse_marker('sys_platform == "darwin" and implementation_name == "cpython"')

    intersection = m.intersect(
        parse_marker('python_version >= "3.6" and os_name == "Windows"')
    )
    assert (
        str(intersection)
        == 'sys_platform == "darwin" and implementation_name == "cpython" '
        'and python_version >= "3.6" and os_name == "Windows"'
    )


def test_multi_marker_intersect_multi_with_overlapping_constraints() -> None:
    m = parse_marker('sys_platform == "darwin" and python_version < "3.6"')

    intersection = m.intersect(
        parse_marker(
            'python_version <= "3.4" and os_name == "Windows" and sys_platform =='
            ' "darwin"'
        )
    )
    assert (
        str(intersection)
        == 'sys_platform == "darwin" and python_version <= "3.4" and os_name =='
        ' "Windows"'
    )


def test_multi_marker_intersect_with_union_drops_union() -> None:
    m = parse_marker('python_version >= "3" and python_version < "4"')
    m2 = parse_marker('python_version < "2" or python_version >= "3"')
    assert str(m.intersect(m2)) == str(m)
    assert str(m2.intersect(m)) == str(m)


def test_multi_marker_intersect_with_multi_union_leads_to_empty_in_one_step() -> None:
    # empty marker in one step
    # py == 2 and (py < 2 or py >= 3) -> empty
    m = parse_marker('sys_platform == "darwin" and python_version == "2"')
    m2 = parse_marker(
        'sys_platform == "darwin" and (python_version < "2" or python_version >= "3")'
    )
    assert m.intersect(m2).is_empty()
    assert m2.intersect(m).is_empty()


def test_multi_marker_intersect_with_multi_union_leads_to_empty_in_two_steps() -> None:
    # empty marker in two steps
    # py >= 2 and (py < 2 or py >= 3) -> py >= 3
    # py < 3 and py >= 3 -> empty
    m = parse_marker('python_version >= "2" and python_version < "3"')
    m2 = parse_marker(
        'sys_platform == "darwin" and (python_version < "2" or python_version >= "3")'
    )
    assert m.intersect(m2).is_empty()
    assert m2.intersect(m).is_empty()


def test_multi_marker_union_multi() -> None:
    m = parse_marker('sys_platform == "darwin" and implementation_name == "cpython"')

    union = m.union(parse_marker('python_version >= "3.6" and os_name == "Windows"'))
    assert (
        str(union)
        == 'sys_platform == "darwin" and implementation_name == "cpython" '
        'or python_version >= "3.6" and os_name == "Windows"'
    )


def test_multi_marker_union_multi_is_single_marker() -> None:
    m = parse_marker('python_version >= "3" and sys_platform == "win32"')
    m2 = parse_marker('sys_platform != "win32" and python_version >= "3"')
    assert str(m.union(m2)) == 'python_version >= "3"'
    assert str(m2.union(m)) == 'python_version >= "3"'


@pytest.mark.parametrize(
    "marker1, marker2, expected",
    [
        (
            'python_version >= "3" and sys_platform == "win32"',
            'python_version >= "3" and sys_platform != "win32" and sys_platform !='
            ' "linux"',
            'python_version >= "3" and sys_platform != "linux"',
        ),
        (
            'python_version >= "3.8" and python_version < "4.0" and sys_platform =='
            ' "win32"',
            'python_version >= "3.8" and python_version < "4.0"',
            'python_version >= "3.8" and python_version < "4.0"',
        ),
    ],
)
def test_multi_marker_union_multi_is_multi(
    marker1: str, marker2: str, expected: str
) -> None:
    m1 = parse_marker(marker1)
    m2 = parse_marker(marker2)
    assert str(m1.union(m2)) == expected
    assert str(m2.union(m1)) == expected


def test_multi_marker_union_with_union() -> None:
    m = parse_marker('sys_platform == "darwin" and implementation_name == "cpython"')

    union = m.union(parse_marker('python_version >= "3.6" or os_name == "Windows"'))
    assert (
        str(union)
        == 'python_version >= "3.6" or os_name == "Windows"'
        ' or sys_platform == "darwin" and implementation_name == "cpython"'
    )


def test_multi_marker_union_with_multi_union_is_single_marker() -> None:
    m = parse_marker('sys_platform == "darwin" and python_version == "3"')
    m2 = parse_marker(
        'sys_platform == "darwin" and python_version < "3" or sys_platform == "darwin"'
        ' and python_version > "3"'
    )
    assert str(m.union(m2)) == 'sys_platform == "darwin"'
    assert str(m2.union(m)) == 'sys_platform == "darwin"'


def test_multi_marker_union_with_union_multi_is_single_marker() -> None:
    m = parse_marker('sys_platform == "darwin" and python_version == "3"')
    m2 = parse_marker(
        'sys_platform == "darwin" and (python_version < "3" or python_version > "3")'
    )
    assert str(m.union(m2)) == 'sys_platform == "darwin"'
    assert str(m2.union(m)) == 'sys_platform == "darwin"'


def test_marker_union() -> None:
    m = parse_marker('sys_platform == "darwin" or implementation_name == "cpython"')

    assert isinstance(m, MarkerUnion)
    assert m.markers == [
        parse_marker('sys_platform == "darwin"'),
        parse_marker('implementation_name == "cpython"'),
    ]


def test_marker_union_deduplicate() -> None:
    m = parse_marker(
        'sys_platform == "darwin" or implementation_name == "cpython" or sys_platform'
        ' == "darwin"'
    )

    assert str(m) == 'sys_platform == "darwin" or implementation_name == "cpython"'


def test_marker_union_of_python_version_and_python_full_version() -> None:
    m = parse_marker('python_version >= "3.6"')
    m2 = parse_marker('python_full_version >= "3.0.0"')
    union = m.union(m2)

    assert str(union) == 'python_full_version >= "3.0.0"'


def test_marker_union_intersect_single_marker() -> None:
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    intersection = m.intersect(parse_marker('implementation_name == "cpython"'))
    assert (
        str(intersection)
        == 'sys_platform == "darwin" and implementation_name == "cpython" '
        'or python_version < "3.4" and implementation_name == "cpython"'
    )


def test_marker_union_intersect_single_with_overlapping_constraints() -> None:
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    intersection = m.intersect(parse_marker('python_version <= "3.6"'))
    assert (
        str(intersection)
        == 'sys_platform == "darwin" and python_version <= "3.6" or python_version <'
        ' "3.4"'
    )

    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')
    intersection = m.intersect(parse_marker('sys_platform == "darwin"'))
    assert str(intersection) == 'sys_platform == "darwin"'


def test_marker_union_intersect_marker_union() -> None:
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    intersection = m.intersect(
        parse_marker('implementation_name == "cpython" or os_name == "Windows"')
    )
    assert (
        str(intersection)
        == 'sys_platform == "darwin" and implementation_name == "cpython" '
        'or sys_platform == "darwin" and os_name == "Windows" or '
        'python_version < "3.4" and implementation_name == "cpython" or '
        'python_version < "3.4" and os_name == "Windows"'
    )


def test_marker_union_intersect_marker_union_drops_unnecessary_markers() -> None:
    m = parse_marker(
        'python_version >= "2.7" and python_version < "2.8" '
        'or python_version >= "3.4" and python_version < "4.0"'
    )
    m2 = parse_marker(
        'python_version >= "2.7" and python_version < "2.8" '
        'or python_version >= "3.4" and python_version < "4.0"'
    )

    intersection = m.intersect(m2)
    expected = (
        'python_version >= "2.7" and python_version < "2.8" '
        'or python_version >= "3.4" and python_version < "4.0"'
    )
    assert str(intersection) == expected


def test_marker_union_intersect_multi_marker() -> None:
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    intersection = m.intersect(
        parse_marker('implementation_name == "cpython" and os_name == "Windows"')
    )
    assert (
        str(intersection)
        == 'implementation_name == "cpython" and os_name == "Windows" and sys_platform'
        ' == "darwin" or implementation_name == "cpython" and os_name == "Windows"'
        ' and python_version < "3.4"'
    )


def test_marker_union_union_with_union() -> None:
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    union = m.union(
        parse_marker('implementation_name == "cpython" or os_name == "Windows"')
    )
    assert (
        str(union)
        == 'sys_platform == "darwin" or python_version < "3.4" '
        'or implementation_name == "cpython" or os_name == "Windows"'
    )


def test_marker_union_union_duplicates() -> None:
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    union = m.union(parse_marker('sys_platform == "darwin" or os_name == "Windows"'))
    assert (
        str(union)
        == 'sys_platform == "darwin" or python_version < "3.4" or os_name == "Windows"'
    )

    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    union = m.union(
        parse_marker(
            'sys_platform == "darwin" or os_name == "Windows" or python_version <='
            ' "3.6"'
        )
    )
    assert (
        str(union)
        == 'sys_platform == "darwin" or python_version <= "3.6" or os_name == "Windows"'
    )


def test_marker_union_all_any() -> None:
    union = MarkerUnion(parse_marker(""), parse_marker(""))

    assert union.is_any()


def test_marker_union_not_all_any() -> None:
    union = MarkerUnion(parse_marker(""), parse_marker(""), parse_marker("<empty>"))

    assert union.is_any()


def test_marker_union_all_empty() -> None:
    union = MarkerUnion(parse_marker("<empty>"), parse_marker("<empty>"))

    assert union.is_empty()


def test_marker_union_not_all_empty() -> None:
    union = MarkerUnion(
        parse_marker("<empty>"), parse_marker("<empty>"), parse_marker("")
    )

    assert not union.is_empty()


def test_marker_str_conversion_skips_empty_and_any() -> None:
    union = MarkerUnion(
        parse_marker("<empty>"),
        parse_marker(
            'sys_platform == "darwin" or python_version <= "3.6" or os_name =='
            ' "Windows"'
        ),
        parse_marker(""),
    )

    assert (
        str(union)
        == 'sys_platform == "darwin" or python_version <= "3.6" or os_name == "Windows"'
    )


def test_intersect_compacts_constraints() -> None:
    m = parse_marker('python_version < "4.0"')

    intersection = m.intersect(parse_marker('python_version < "5.0"'))
    assert str(intersection) == 'python_version < "4.0"'


def test_multi_marker_removes_duplicates() -> None:
    m = parse_marker('sys_platform == "win32" and sys_platform == "win32"')

    assert str(m) == 'sys_platform == "win32"'

    m = parse_marker(
        'sys_platform == "darwin" and implementation_name == "cpython" '
        'and sys_platform == "darwin" and implementation_name == "cpython"'
    )

    assert str(m) == 'sys_platform == "darwin" and implementation_name == "cpython"'


@pytest.mark.parametrize(
    ("marker_string", "environment", "expected"),
    [
        (f"os_name == '{os.name}'", None, True),
        ("os_name == 'foo'", {"os_name": "foo"}, True),
        ("os_name == 'foo'", {"os_name": "bar"}, False),
        ("'2.7' in python_version", {"python_version": "2.7.5"}, True),
        ("'2.7' not in python_version", {"python_version": "2.7"}, False),
        (
            "os_name == 'foo' and python_version ~= '2.7.0'",
            {"os_name": "foo", "python_version": "2.7.6"},
            True,
        ),
        (
            "python_version ~= '2.7.0' and (os_name == 'foo' or os_name == 'bar')",
            {"os_name": "foo", "python_version": "2.7.4"},
            True,
        ),
        (
            "python_version ~= '2.7.0' and (os_name == 'foo' or os_name == 'bar')",
            {"os_name": "bar", "python_version": "2.7.4"},
            True,
        ),
        (
            "python_version ~= '2.7.0' and (os_name == 'foo' or os_name == 'bar')",
            {"os_name": "other", "python_version": "2.7.4"},
            False,
        ),
        ("extra == 'security'", {"extra": "quux"}, False),
        ("extra == 'security'", {"extra": "security"}, True),
        (f"os.name == '{os.name}'", None, True),
        ("sys.platform == 'win32'", {"sys_platform": "linux2"}, False),
        ("platform.version in 'Ubuntu'", {"platform_version": "#39"}, False),
        ("platform.machine=='x86_64'", {"platform_machine": "x86_64"}, True),
        (
            "platform.python_implementation=='Jython'",
            {"platform_python_implementation": "CPython"},
            False,
        ),
        (
            "python_version == '2.5' and platform.python_implementation!= 'Jython'",
            {"python_version": "2.7"},
            False,
        ),
        (
            "platform_machine in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE amd64"
            " AMD64 win32 WIN32'",
            {"platform_machine": "foo"},
            False,
        ),
        (
            "platform_machine in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE amd64"
            " AMD64 win32 WIN32'",
            {"platform_machine": "x86_64"},
            True,
        ),
        (
            "platform_machine not in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE"
            " amd64 AMD64 win32 WIN32'",
            {"platform_machine": "foo"},
            True,
        ),
        (
            "platform_machine not in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE"
            " amd64 AMD64 win32 WIN32'",
            {"platform_machine": "x86_64"},
            False,
        ),
    ],
)
def test_validate(
    marker_string: str, environment: dict[str, str] | None, expected: bool
) -> None:
    m = parse_marker(marker_string)

    assert m.validate(environment) is expected


@pytest.mark.parametrize(
    "marker, env",
    [
        (
            'platform_release >= "9.0" and platform_release < "11.0"',
            {"platform_release": "10.0"},
        )
    ],
)
def test_parse_version_like_markers(marker: str, env: dict[str, str]) -> None:
    m = parse_marker(marker)

    assert m.validate(env)


@pytest.mark.parametrize(
    "marker, expected",
    [
        ('python_version >= "3.6"', 'python_version >= "3.6"'),
        ('python_version >= "3.6" and extra == "foo"', 'python_version >= "3.6"'),
        (
            'python_version >= "3.6" and (extra == "foo" or extra == "bar")',
            'python_version >= "3.6"',
        ),
        (
            'python_version >= "3.6" and (extra == "foo" or extra == "bar") or'
            ' implementation_name == "pypy"',
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
        (
            'python_version >= "3.6" and extra == "foo" or implementation_name =='
            ' "pypy" and extra == "bar"',
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
        (
            'python_version >= "3.6" or extra == "foo" and implementation_name =='
            ' "pypy" or extra == "bar"',
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
    ],
)
def test_without_extras(marker: str, expected: str) -> None:
    m = parse_marker(marker)

    assert str(m.without_extras()) == expected


@pytest.mark.parametrize(
    "marker, excluded, expected",
    [
        ('python_version >= "3.6"', "implementation_name", 'python_version >= "3.6"'),
        ('python_version >= "3.6"', "python_version", "*"),
        (
            'python_version >= "3.6" and extra == "foo"',
            "extra",
            'python_version >= "3.6"',
        ),
        (
            'python_version >= "3.6" and (extra == "foo" or extra == "bar")',
            "python_version",
            'extra == "foo" or extra == "bar"',
        ),
        (
            'python_version >= "3.6" and (extra == "foo" or extra == "bar") or'
            ' implementation_name == "pypy"',
            "python_version",
            'extra == "foo" or extra == "bar" or implementation_name == "pypy"',
        ),
        (
            'python_version >= "3.6" and extra == "foo" or implementation_name =='
            ' "pypy" and extra == "bar"',
            "implementation_name",
            'python_version >= "3.6" and extra == "foo" or extra == "bar"',
        ),
        (
            'python_version >= "3.6" or extra == "foo" and implementation_name =='
            ' "pypy" or extra == "bar"',
            "implementation_name",
            'python_version >= "3.6" or extra == "foo" or extra == "bar"',
        ),
        (
            'extra == "foo" and python_version >= "3.6" or python_version >= "3.6"',
            "extra",
            'python_version >= "3.6"',
        ),
    ],
)
def test_exclude(marker: str, excluded: str, expected: str) -> None:
    m = parse_marker(marker)

    if expected == "*":
        assert m.exclude(excluded).is_any()
    else:
        assert str(m.exclude(excluded)) == expected


@pytest.mark.parametrize(
    "marker, only, expected",
    [
        ('python_version >= "3.6"', ["python_version"], 'python_version >= "3.6"'),
        ('python_version >= "3.6"', ["sys_platform"], ""),
        (
            'python_version >= "3.6" and extra == "foo"',
            ["python_version"],
            'python_version >= "3.6"',
        ),
        (
            'python_version >= "3.6" and (extra == "foo" or extra == "bar")',
            ["extra"],
            'extra == "foo" or extra == "bar"',
        ),
        (
            'python_version >= "3.6" and (extra == "foo" or extra == "bar") or'
            ' implementation_name == "pypy"',
            ["implementation_name"],
            'implementation_name == "pypy"',
        ),
        (
            'python_version >= "3.6" and extra == "foo" or implementation_name =='
            ' "pypy" and extra == "bar"',
            ["implementation_name"],
            'implementation_name == "pypy"',
        ),
        (
            'python_version >= "3.6" or extra == "foo" and implementation_name =='
            ' "pypy" or extra == "bar"',
            ["implementation_name"],
            'implementation_name == "pypy"',
        ),
        (
            'python_version >= "3.6" or extra == "foo" and implementation_name =='
            ' "pypy" or extra == "bar"',
            ["implementation_name", "python_version"],
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
    ],
)
def test_only(marker: str, only: list[str], expected: str) -> None:
    m = parse_marker(marker)

    assert str(m.only(*only)) == expected


def test_union_of_a_single_marker_is_the_single_marker() -> None:
    union = MarkerUnion.of(SingleMarker("python_version", ">= 2.7"))

    assert SingleMarker("python_version", ">= 2.7") == union


def test_union_of_multi_with_a_containing_single() -> None:
    single = parse_marker('python_version >= "2.7"')
    multi = parse_marker('python_version >= "2.7" and extra == "foo"')
    union = multi.union(single)

    assert union == single


@pytest.mark.parametrize(
    "marker, inverse",
    [
        ('implementation_name == "pypy"', 'implementation_name != "pypy"'),
        ('implementation_name === "pypy"', 'implementation_name != "pypy"'),
        ('implementation_name != "pypy"', 'implementation_name == "pypy"'),
        ('python_version in "2.7, 3.0, 3.1"', 'python_version not in "2.7, 3.0, 3.1"'),
        ('python_version not in "2.7, 3.0, 3.1"', 'python_version in "2.7, 3.0, 3.1"'),
        ('python_version < "3.6"', 'python_version >= "3.6"'),
        ('python_version >= "3.6"', 'python_version < "3.6"'),
        ('python_version <= "3.6"', 'python_version > "3.6"'),
        ('python_version > "3.6"', 'python_version <= "3.6"'),
        (
            'python_version > "3.6" or implementation_name == "pypy"',
            'python_version <= "3.6" and implementation_name != "pypy"',
        ),
        (
            'python_version <= "3.6" and implementation_name != "pypy"',
            'python_version > "3.6" or implementation_name == "pypy"',
        ),
        (
            'python_version ~= "3.6"',
            'python_version < "3.6" or python_version >= "4.0"',
        ),
        (
            'python_version ~= "3.6.3"',
            'python_version < "3.6.3" or python_version >= "3.7.0"',
        ),
    ],
)
def test_invert(marker: str, inverse: str) -> None:
    m = parse_marker(marker)

    assert parse_marker(inverse) == m.invert()


@pytest.mark.parametrize(
    "marker, expected",
    [
        (
            'python_version >= "3.6" or python_version < "3.7" or python_version <'
            ' "3.6"',
            'python_version >= "3.6" or python_version < "3.7"',
        ),
    ],
)
def test_union_should_drop_markers_if_their_complement_is_present(
    marker: str, expected: str
) -> None:
    m = parse_marker(marker)

    assert parse_marker(expected) == m


@pytest.mark.parametrize(
    "scheme, marker, expected",
    [
        ("empty", EmptyMarker(), EmptyMarker()),
        ("any", AnyMarker(), AnyMarker()),
        (
            "A_",
            SingleMarker("python_version", ">=3.7"),
            SingleMarker("python_version", ">=3.7"),
        ),
        (
            "AB_",
            MultiMarker(
                SingleMarker("python_version", ">=3.7"),
                SingleMarker("python_version", "<3.9"),
            ),
            MultiMarker(
                SingleMarker("python_version", ">=3.7"),
                SingleMarker("python_version", "<3.9"),
            ),
        ),
        (
            "A+B_",
            MarkerUnion(
                SingleMarker("python_version", "<3.7"),
                SingleMarker("python_version", ">=3.9"),
            ),
            MarkerUnion(
                SingleMarker("python_version", "<3.7"),
                SingleMarker("python_version", ">=3.9"),
            ),
        ),
        (
            "AB+AC_",
            MarkerUnion(
                MultiMarker(
                    SingleMarker("python_version", ">=3.7"),
                    SingleMarker("python_version", "<3.9"),
                ),
                MultiMarker(
                    SingleMarker("python_version", ">=3.7"),
                    SingleMarker("sys_platform", "linux"),
                ),
            ),
            MarkerUnion(
                MultiMarker(
                    SingleMarker("python_version", ">=3.7"),
                    SingleMarker("python_version", "<3.9"),
                ),
                MultiMarker(
                    SingleMarker("python_version", ">=3.7"),
                    SingleMarker("sys_platform", "linux"),
                ),
            ),
        ),
        (
            "A(B+C)_AB+AC",
            MultiMarker(
                SingleMarker("python_version", ">=3.7"),
                MarkerUnion(
                    SingleMarker("python_version", "<3.9"),
                    SingleMarker("sys_platform", "linux"),
                ),
            ),
            MarkerUnion(
                MultiMarker(
                    SingleMarker("python_version", ">=3.7"),
                    SingleMarker("python_version", "<3.9"),
                ),
                MultiMarker(
                    SingleMarker("python_version", ">=3.7"),
                    SingleMarker("sys_platform", "linux"),
                ),
            ),
        ),
        (
            "(A+B)(C+D)_AC+AD+BC+BD",
            MultiMarker(
                MarkerUnion(
                    SingleMarker("python_version", ">=3.7"),
                    SingleMarker("sys_platform", "win32"),
                ),
                MarkerUnion(
                    SingleMarker("python_version", "<3.9"),
                    SingleMarker("sys_platform", "linux"),
                ),
            ),
            MarkerUnion(
                MultiMarker(
                    SingleMarker("python_version", ">=3.7"),
                    SingleMarker("python_version", "<3.9"),
                ),
                MultiMarker(
                    SingleMarker("python_version", ">=3.7"),
                    SingleMarker("sys_platform", "linux"),
                ),
                MultiMarker(
                    SingleMarker("sys_platform", "win32"),
                    SingleMarker("python_version", "<3.9"),
                ),
            ),
        ),
        (
            "A(B+C)+(D+E)(F+G)_AB+AC+DF+DG+EF+DG",
            MarkerUnion(
                MultiMarker(
                    SingleMarker("sys_platform", "win32"),
                    MarkerUnion(
                        SingleMarker("python_version", "<3.7"),
                        SingleMarker("python_version", ">=3.9"),
                    ),
                ),
                MultiMarker(
                    MarkerUnion(
                        SingleMarker("python_version", "<3.8"),
                        SingleMarker("python_version", ">=3.9"),
                    ),
                    MarkerUnion(
                        SingleMarker("sys_platform", "linux"),
                        SingleMarker("python_version", ">=3.9"),
                    ),
                ),
            ),
            MarkerUnion(
                MultiMarker(
                    SingleMarker("sys_platform", "win32"),
                    SingleMarker("python_version", "<3.7"),
                ),
                SingleMarker("python_version", ">=3.9"),
                MultiMarker(
                    SingleMarker("python_version", "<3.8"),
                    SingleMarker("sys_platform", "linux"),
                ),
            ),
        ),
        (
            "(A+B(C+D))(E+F)_AE+AF+BCE+BCF+BDE+BDF",
            MultiMarker(
                MarkerUnion(
                    SingleMarker("python_version", ">=3.9"),
                    MultiMarker(
                        SingleMarker("implementation_name", "cpython"),
                        MarkerUnion(
                            SingleMarker("python_version", "<3.7"),
                            SingleMarker("python_version", ">=3.8"),
                        ),
                    ),
                ),
                MarkerUnion(
                    SingleMarker("sys_platform", "win32"),
                    SingleMarker("sys_platform", "linux"),
                ),
            ),
            MarkerUnion(
                MultiMarker(
                    SingleMarker("python_version", ">=3.9"),
                    SingleMarker("sys_platform", "win32"),
                ),
                MultiMarker(
                    SingleMarker("python_version", ">=3.9"),
                    SingleMarker("sys_platform", "linux"),
                ),
                MultiMarker(
                    SingleMarker("implementation_name", "cpython"),
                    SingleMarker("python_version", "<3.7"),
                    SingleMarker("sys_platform", "win32"),
                ),
                MultiMarker(
                    SingleMarker("implementation_name", "cpython"),
                    SingleMarker("python_version", "<3.7"),
                    SingleMarker("sys_platform", "linux"),
                ),
                MultiMarker(
                    SingleMarker("implementation_name", "cpython"),
                    SingleMarker("python_version", ">=3.8"),
                    SingleMarker("sys_platform", "win32"),
                ),
                MultiMarker(
                    SingleMarker("implementation_name", "cpython"),
                    SingleMarker("python_version", ">=3.8"),
                    SingleMarker("sys_platform", "linux"),
                ),
            ),
        ),
    ],
)
def test_dnf(scheme: str, marker: BaseMarker, expected: BaseMarker) -> None:
    assert dnf(marker) == expected
