from __future__ import annotations

import os

from typing import TYPE_CHECKING

import pytest

from poetry.core.constraints.generic import UnionConstraint
from poetry.core.constraints.generic import parse_constraint as parse_generic_constraint
from poetry.core.constraints.version import parse_constraint as parse_version_constraint
from poetry.core.version.markers import AnyMarker
from poetry.core.version.markers import AtomicMarkerUnion
from poetry.core.version.markers import EmptyMarker
from poetry.core.version.markers import InvalidMarkerError
from poetry.core.version.markers import MarkerUnion
from poetry.core.version.markers import MultiMarker
from poetry.core.version.markers import SingleMarker
from poetry.core.version.markers import cnf
from poetry.core.version.markers import dnf
from poetry.core.version.markers import intersection
from poetry.core.version.markers import parse_marker
from poetry.core.version.markers import union


if TYPE_CHECKING:
    from poetry.core.version.markers import BaseMarker

EMPTY = "<empty>"


@pytest.mark.parametrize(
    "marker",
    [
        'sys_platform == "linux" or sys_platform == "win32"',
        'sys_platform == "win32" or sys_platform == "linux"',
        (
            'sys_platform == "linux" or sys_platform == "win32"'
            ' or sys_platform == "darwin"'
        ),
        (
            'python_version >= "3.6" and extra == "foo"'
            ' or implementation_name == "pypy" and extra == "bar"'
        ),
        (
            'python_version < "3.9" or python_version >= "3.10"'
            ' and sys_platform == "linux" or sys_platform == "win32"'
        ),
        (
            'sys_platform == "win32" and python_version < "3.6" or sys_platform =='
            ' "linux" and python_version < "3.6" and python_version >= "3.3" or'
            ' sys_platform == "darwin" and python_version < "3.3"'
        ),
        # "extra" is a special marker that can have multiple values at the same time.
        # Thus, "extra == 'a' and extra == 'b'" is not empty.
        # Further, "extra == 'a' and extra != 'b'" cannot be simplified
        # because it has the meaning "extra 'a' must and extra 'b' must not be active"
        'extra == "a" and extra == "b"',
        'extra == "a" and extra != "b"',
        'extra != "a" and extra == "b"',
        'extra != "a" and extra != "b"',
        'extra == "a" and extra == "b" and extra != "c" and extra != "d"',
        'extra == "a" or extra == "b"',
        'extra == "a" or extra != "b"',
        'extra != "a" or extra == "b"',
        'extra != "a" or extra != "b"',
        'extra == "a" or extra == "b" or extra != "c" or extra != "d"',
        # String comparison markers
        '"tegra" in platform_release',
        '"tegra" not in platform_release',
        '"tegra" in platform_release or "rpi-v8" in platform_release',
        '"tegra" not in platform_release and "rpi-v8" not in platform_release',
    ],
)
def test_parse_marker(marker: str) -> None:
    assert str(parse_marker(marker)) == marker


@pytest.mark.parametrize(
    ("marker", "valid"),
    [
        ('platform_release != "4.9.253-tegra"', True),
        ('python_version != "4.9.253-tegra"', False),
    ],
)
def test_parse_marker_non_python_versions(marker: str, valid: bool) -> None:
    if valid:
        assert str(parse_marker(marker)) == marker
    else:
        with pytest.raises(InvalidMarkerError):
            parse_marker(marker)


@pytest.mark.parametrize(
    ("marker", "expected_name", "expected_constraint"),
    [
        ('sys_platform == "darwin"', "sys_platform", "darwin"),
        (
            'python_version in "2.7, 3.0, 3.1"',
            "python_version",
            ">=2.7,<2.8 || >=3.0,<3.2",
        ),
        ('"2.7" in python_version', "python_version", ">=2.7,<2.8"),
        (
            'python_version not in "2.7, 3.0, 3.1"',
            "python_version",
            "<2.7 || >=2.8,<3.0 || >=3.2",
        ),
        (
            (
                "platform_machine in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE"
                " amd64 AMD64 win32 WIN32'"
            ),
            "platform_machine",
            (
                "x86_64 || X86_64 || aarch64 || AARCH64 || ppc64le || PPC64LE || amd64"
                " || AMD64 || win32 || WIN32"
            ),
        ),
        (
            (
                "platform_machine not in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE"
                " amd64 AMD64 win32 WIN32'"
            ),
            "platform_machine",
            (
                "!=x86_64, !=X86_64, !=aarch64, !=AARCH64, !=ppc64le, !=PPC64LE,"
                " !=amd64, !=AMD64, !=win32, !=WIN32"
            ),
        ),
        (
            'platform_machine not in "aarch64|loongarch64"',
            "platform_machine",
            "!=aarch64, !=loongarch64",
        ),
        ('"tegra" not in platform_release', "platform_release", "'tegra' not in"),
        ('"rpi-v8" in platform_release', "platform_release", "'rpi-v8' in"),
        ('"arm" not in platform_version', "platform_version", "'arm' not in"),
        ('"arm" in platform_version', "platform_version", "'arm' in"),
    ],
)
def test_parse_single_marker(
    marker: str, expected_name: str, expected_constraint: str
) -> None:
    m = parse_marker(marker)

    assert isinstance(m, SingleMarker)
    assert m.name == expected_name
    assert str(m.constraint) == expected_constraint


def test_single_marker_normalisation() -> None:
    m1 = SingleMarker("python_version", ">=3.6")
    m2 = SingleMarker("python_version", ">= 3.6")
    assert m1 == m2
    assert hash(m1) == hash(m2)


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


@pytest.mark.parametrize(
    ("marker1", "marker2"),
    [
        ('sys_platform == "win32"', 'sys_platform == "linux"'),
        ('sys_platform != "win32"', 'sys_platform == "win32"'),
        ('python_version >= "3.6"', 'python_version < "3.6"'),
        ('python_version == "3.6"', 'python_version == "3.7"'),
        ('python_version > "3.6"', 'python_version <= "3.6"'),
        ('python_version >= "3.6"', 'python_version < "3.6"'),
        ('python_version > "3.6"', 'python_version < "3.7"'),
    ],
)
def test_single_marker_intersect_is_empty(marker1: str, marker2: str) -> None:
    assert parse_marker(marker1).intersect(parse_marker(marker2)).is_empty()


@pytest.mark.parametrize(
    ("marker1", "marker2", "expected"),
    [
        ('python_version < "3.6"', 'python_version < "3.4"', 'python_version < "3.4"'),
        (
            'python_version >= "3.6"',
            'python_version < "3.7"',
            'python_version == "3.6"',
        ),
    ],
)
def test_single_marker_intersect_is_single_marker(
    marker1: str, marker2: str, expected: str
) -> None:
    m = parse_marker(marker1)

    intersection = m.intersect(parse_marker(marker2))
    assert str(intersection) == expected


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


@pytest.mark.parametrize(
    ("marker1", "marker2", "expected"),
    [
        # same value
        ('extra == "a"', 'extra == "a"', 'extra == "a"'),
        ('extra == "a"', 'extra != "a"', "<empty>"),
        ('extra != "a"', 'extra == "a"', "<empty>"),
        ('extra != "a"', 'extra != "a"', 'extra != "a"'),
        # different values
        ('extra == "a"', 'extra == "b"', 'extra == "a" and extra == "b"'),
        ('extra == "a"', 'extra != "b"', 'extra == "a" and extra != "b"'),
        ('extra != "a"', 'extra == "b"', 'extra != "a" and extra == "b"'),
        ('extra != "a"', 'extra != "b"', 'extra != "a" and extra != "b"'),
        # AtomicMultiMarker
        (
            'extra == "a" and extra == "b"',
            'extra == "c"',
            'extra == "a" and extra == "b" and extra == "c"',
        ),
        (
            'extra != "a" and extra != "b"',
            'extra != "c"',
            'extra != "a" and extra != "b" and extra != "c"',
        ),
        (
            'extra != "a" and extra != "b"',
            'extra == "c"',
            'extra != "a" and extra != "b" and extra == "c"',
        ),
        (
            'extra == "a" and extra == "b"',
            'extra != "c"',
            'extra == "a" and extra == "b" and extra != "c"',
        ),
        (
            'extra == "a" and extra == "b"',
            'extra == "a" and extra == "b"',
            'extra == "a" and extra == "b"',
        ),
        (
            'extra == "a" and extra == "b"',
            'extra == "b" and extra == "a"',
            'extra == "a" and extra == "b"',
        ),
        (
            'extra == "a" and extra == "b"',
            'extra == "a" and extra == "b" and extra == "c"',
            'extra == "a" and extra == "b" and extra == "c"',
        ),
        (
            'extra == "a" and extra == "b" and extra == "c" and extra == "d"',
            'extra == "a" and extra == "b"',
            'extra == "a" and extra == "b" and extra == "c" and extra == "d"',
        ),
        (
            'extra == "a" and extra == "b"',
            'extra == "c" and extra != "d"',
            'extra == "a" and extra == "b" and extra == "c" and extra != "d"',
        ),
        ('extra != "a" and extra != "b"', 'extra == "a"', "<empty>"),
        ('extra != "a" and extra == "b"', 'extra == "a" and extra == "c"', "<empty>"),
        (
            'extra != "a" and extra != "b"',
            'extra != "a"',
            'extra != "a" and extra != "b"',
        ),
        (
            'extra == "a" and extra != "b"',
            'extra == "a"',
            'extra == "a" and extra != "b"',
        ),
        # AtomicMarkerUnion
        (
            'extra == "a" or extra == "b"',
            'extra == "c"',
            '(extra == "a" or extra == "b") and extra == "c"',
        ),
        (
            'extra == "a" or extra == "b"',
            'extra != "c"',
            '(extra == "a" or extra == "b") and extra != "c"',
        ),
        ('extra == "a" or extra == "b"', 'extra == "a"', 'extra == "a"'),
        ('extra != "a" or extra == "b"', 'extra != "a"', 'extra != "a"'),
        (
            'extra == "a" or extra == "b"',
            'extra != "a"',
            'extra == "b" and extra != "a"',
        ),
        (
            'extra == "a" or extra == "b"',
            'extra == "a" or extra == "b"',
            'extra == "a" or extra == "b"',
        ),
        (
            'extra == "a" or extra == "b"',
            'extra == "b" or extra == "a"',
            'extra == "a" or extra == "b"',
        ),
        (
            'extra == "a" or extra == "b"',
            'extra == "a" or extra == "b" or extra == "c"',
            'extra == "a" or extra == "b"',
        ),
        (
            'extra == "a" or extra == "b" or extra == "c" or extra == "d"',
            'extra == "a" or extra == "b"',
            'extra == "a" or extra == "b"',
        ),
        (
            'extra == "a" or extra == "b"',
            'extra == "a" or extra != "c"',
            '(extra == "a" or extra == "b") and (extra == "a" or extra != "c")',
        ),
        # AtomicMultiMarker and AtomicMarkerUnion
        (
            'extra != "a" and extra != "b"',
            'extra == "a" or extra == "b"',
            "<empty>",
        ),
        (
            'extra != "a" and extra != "b"',
            'extra == "a" or extra == "c"',
            'extra == "c" and extra != "a" and extra != "b"',
        ),
        (
            'extra == "a" and extra == "b"',
            'extra == "a" or extra == "b"',
            'extra == "a" and extra == "b"',
        ),
        (
            'extra == "a" or extra == "b"',
            'extra == "a" and extra == "b"',
            'extra == "a" and extra == "b"',
        ),
    ],
)
def test_single_marker_intersect_extras(
    marker1: str, marker2: str, expected: str
) -> None:
    assert str(parse_marker(marker1).intersect(parse_marker(marker2))) == expected


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
        (
            'python_version == "3.6"',
            'python_version >= "3.7"',
            'python_version >= "3.6"',
        ),
        (
            'python_version <= "3.6"',
            'python_version >= "3.7"',
            "",
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
        str(union) == 'implementation_name == "cpython" and python_version >= "3.6" or'
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
    m1 = parse_marker(single_marker)
    m2 = parse_marker(multi_marker)
    assert str(m1.union(m2)) == expected
    assert str(m2.union(m1)) == expected


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


@pytest.mark.parametrize(
    ("marker1", "marker2", "expected"),
    [
        # same value
        ('extra == "a"', 'extra == "a"', 'extra == "a"'),
        ('extra == "a"', 'extra != "a"', ""),
        ('extra != "a"', 'extra == "a"', ""),
        ('extra != "a"', 'extra != "a"', 'extra != "a"'),
        # different values
        ('extra == "a"', 'extra == "b"', 'extra == "a" or extra == "b"'),
        ('extra == "a"', 'extra != "b"', 'extra == "a" or extra != "b"'),
        ('extra != "a"', 'extra == "b"', 'extra != "a" or extra == "b"'),
        ('extra != "a"', 'extra != "b"', 'extra != "a" or extra != "b"'),
        # AtomicMultiMarker
        (
            'extra == "a" and extra == "b"',
            'extra == "c"',
            'extra == "a" and extra == "b" or extra == "c"',
        ),
        (
            'extra != "a" and extra != "b"',
            'extra != "c"',
            'extra != "a" and extra != "b" or extra != "c"',
        ),
        (
            'extra != "a" and extra != "b"',
            'extra == "c"',
            'extra != "a" and extra != "b" or extra == "c"',
        ),
        (
            'extra == "a" and extra == "b"',
            'extra != "c"',
            'extra == "a" and extra == "b" or extra != "c"',
        ),
        (
            'extra == "a" and extra == "b"',
            'extra == "a" and extra == "b"',
            'extra == "a" and extra == "b"',
        ),
        (
            'extra == "a" and extra == "b"',
            'extra == "a" and extra == "b" and extra == "c"',
            'extra == "a" and extra == "b"',
        ),
        (
            'extra == "a" and extra == "b" and extra == "c" and extra == "d"',
            'extra == "a" and extra == "b"',
            'extra == "a" and extra == "b"',
        ),
        (
            'extra == "a" and extra == "b"',
            'extra == "c" and extra != "d"',
            'extra == "a" and extra == "b" or extra == "c" and extra != "d"',
        ),
        (
            'extra != "a" and extra != "b"',
            'extra == "a"',
            'extra != "b" or extra == "a"',
        ),
        (
            'extra != "a" and extra == "b"',
            'extra == "a" and extra == "c"',
            'extra != "a" and extra == "b" or extra == "a" and extra == "c"',
        ),
        (
            'extra != "a" and extra != "b"',
            'extra != "a"',
            'extra != "a"',
        ),
        (
            'extra == "a" and extra != "b"',
            'extra == "a"',
            'extra == "a"',
        ),
        # AtomicMarkerUnion
        (
            'extra == "a" or extra == "b"',
            'extra == "c"',
            'extra == "a" or extra == "b" or extra == "c"',
        ),
        (
            'extra == "a" or extra == "b"',
            'extra != "c"',
            'extra == "a" or extra == "b" or extra != "c"',
        ),
        (
            'extra == "a" or extra == "b"',
            'extra == "a"',
            'extra == "a" or extra == "b"',
        ),
        (
            'extra != "a" or extra == "b"',
            'extra != "a"',
            'extra != "a" or extra == "b"',
        ),
        (
            'extra == "a" or extra == "b"',
            'extra != "a"',
            "",
        ),
        (
            'extra == "a" or extra == "b"',
            'extra == "a" or extra == "b"',
            'extra == "a" or extra == "b"',
        ),
        (
            'extra == "a" or extra == "b"',
            'extra == "a" or extra == "b" or extra == "c"',
            'extra == "a" or extra == "b" or extra == "c"',
        ),
        (
            'extra == "a" or extra == "b" or extra == "c" or extra == "d"',
            'extra == "a" or extra == "b"',
            'extra == "a" or extra == "b" or extra == "c" or extra == "d"',
        ),
        (
            'extra == "a" or extra == "b"',
            'extra == "a" or extra != "c"',
            'extra == "a" or extra == "b" or extra != "c"',
        ),
        # AtomicMultiMarker and AtomicMarkerUnion
        (
            'extra != "a" and extra != "b"',
            'extra == "a" or extra == "b"',
            'extra != "a" and extra != "b" or extra == "a" or extra == "b"',
        ),
        (
            'extra != "a" and extra != "b"',
            'extra == "a" or extra == "c"',
            'extra != "a" and extra != "b" or extra == "a" or extra == "c"',
        ),
        (
            'extra == "a" or extra == "b"',
            'extra == "a" and extra == "c"',
            'extra == "a" or extra == "b"',
        ),
        (
            'extra == "a" and extra == "c"',
            'extra == "a" or extra == "b"',
            'extra == "a" or extra == "b"',
        ),
    ],
)
def test_single_marker_union_extras(marker1: str, marker2: str, expected: str) -> None:
    assert str(parse_marker(marker1).union(parse_marker(marker2))) == expected


def test_multi_marker() -> None:
    m = parse_marker('sys_platform == "darwin" and implementation_name == "cpython"')

    assert isinstance(m, MultiMarker)
    assert m.markers == (
        parse_marker('sys_platform == "darwin"'),
        parse_marker('implementation_name == "cpython"'),
    )


def test_multi_marker_is_empty_is_contradictory() -> None:
    m = parse_marker(
        'sys_platform == "linux" and python_version >= "3.5" and python_version < "2.8"'
    )

    assert m.is_empty()

    m = parse_marker('sys_platform == "linux" and sys_platform == "win32"')

    assert m.is_empty()


def test_multi_complex_multi_marker_is_empty() -> None:
    m1 = parse_marker(
        'python_full_version >= "3.0.0" and python_full_version < "3.4.0"'
    )
    m2 = parse_marker(
        'python_version >= "3.6" and python_full_version < "3.0.0" and python_version <'
        ' "3.7"'
    )
    m3 = parse_marker(
        'python_version >= "3.6" and python_version < "3.7" and python_full_version >='
        ' "3.5.0"'
    )

    m = m1.intersect(m2.union(m3))

    assert m.is_empty()


def test_multi_marker_is_any() -> None:
    m1 = parse_marker('python_version != "3.6" or python_version == "3.6"')
    m2 = parse_marker('python_version != "3.7" or python_version == "3.7"')

    assert m1.intersect(m2).is_any()
    assert m2.intersect(m1).is_any()


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
        str(union) == 'sys_platform == "darwin" and implementation_name == "cpython" '
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
            (
                'python_version >= "3" and sys_platform != "win32" and sys_platform !='
                ' "linux"'
            ),
            'python_version >= "3" and sys_platform != "linux"',
        ),
        (
            (
                'python_version >= "3.8" and python_version < "4.0" and sys_platform =='
                ' "win32"'
            ),
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


@pytest.mark.parametrize(
    "marker1, marker2, expected",
    [
        # Equivalent ranges
        (
            'python_version == "3.8" or python_version == "3.9"',
            'python_version >= "3.8" and python_version <= "3.9"',
            'python_version >= "3.8" and python_version < "3.10"',
        ),
        (
            'python_version == "3.8" or python_version == "3.9"',
            (
                'python_version >= "3.8" and python_version <= "3.9"'
                ' and sys_platform == "linux"'
            ),
            'python_version >= "3.8" and python_version < "3.10"',
        ),
        (
            'python_version == "3.8" or python_version == "3.9"',
            (
                'python_version >= "3.8" and python_version <= "3.9"'
                ' and sys_platform == "linux"'
            ),
            'python_version >= "3.8" and python_version < "3.10"',
        ),
        (
            'python_version == "3.8" or python_version == "3.9"',
            (
                'python_version >= "3.8" and python_version < "3.10"'
                ' and sys_platform == "linux"'
            ),
            'python_version >= "3.8" and python_version < "3.10"',
        ),
        (
            'python_version == "3.8" or python_version == "3.9"',
            (
                'python_version > "3.7" and python_version < "3.10"'
                ' and sys_platform == "linux"'
            ),
            'python_version > "3.7" and python_version < "3.10"',
        ),
        (
            'python_version == "3.8" or python_version == "3.9"',
            (
                'python_version > "3.7" and python_version <= "3.9"'
                ' and sys_platform == "linux"'
            ),
            'python_version > "3.7" and python_version < "3.10"',
        ),
        (
            (
                'python_version == "3.8" or python_version == "3.9"'
                ' or python_version == "3.10"'
            ),
            (
                'python_version >= "3.8" and python_version <= "3.10"'
                ' and sys_platform == "linux"'
            ),
            'python_version >= "3.8" and python_version <= "3.10"',
        ),
        (
            (
                'python_version == "3.8" or python_version == "3.9"'
                ' or python_version == "3.10"'
            ),
            (
                'python_version >= "3.8" and python_version < "3.11"'
                ' and sys_platform == "linux"'
            ),
            'python_version >= "3.8" and python_version < "3.11"',
        ),
        (
            (
                'python_version == "3.8" or python_version == "3.9"'
                ' or python_version == "3.10"'
            ),
            (
                'python_version > "3.7" and python_version <= "3.10"'
                ' and sys_platform == "linux"'
            ),
            'python_version > "3.7" and python_version <= "3.10"',
        ),
        (
            (
                'python_version == "3.8" or python_version == "3.9"'
                ' or python_version == "3.10"'
            ),
            (
                'python_version > "3.7" and python_version < "3.11"'
                ' and sys_platform == "linux"'
            ),
            'python_version > "3.7" and python_version < "3.11"',
        ),
        # Ranges with same start
        (
            'python_version >= "3.6" and python_full_version < "3.6.2"',
            'python_version >= "3.6" and python_version < "3.7"',
            'python_version == "3.6"',
        ),
        (
            'python_version >= "3.6" and python_full_version < "3.7.2"',
            'python_version >= "3.6" and python_version < "3.8"',
            'python_version >= "3.6" and python_version < "3.8"',
        ),
        (
            'python_version > "3.6" and python_full_version < "3.7.2"',
            'python_version > "3.6" and python_version < "3.8"',
            'python_version > "3.6" and python_version < "3.8"',
        ),
        (
            'python_version > "3.7"',
            'python_version >= "3.8" and sys_platform == "linux"',
            'python_version > "3.7"',
        ),
        # Ranges meet exactly (adjacent ranges)
        (
            'python_version >= "3.6" and python_full_version < "3.6.2"',
            'python_full_version >= "3.6.2" and python_version < "3.7"',
            'python_version == "3.6"',
        ),
        (
            'python_version >= "3.6" and python_full_version < "3.7.2"',
            'python_full_version >= "3.6.2" and python_version < "3.8"',
            'python_version >= "3.6" and python_version < "3.8"',
        ),
        (
            'python_version >= "3.6" and python_full_version <= "3.6.2"',
            'python_full_version > "3.6.2" and python_version < "3.7"',
            'python_version == "3.6"',
        ),
        (
            'python_version >= "3.6" and python_full_version <= "3.7.2"',
            'python_full_version > "3.6.2" and python_version < "3.8"',
            'python_version >= "3.6" and python_version < "3.8"',
        ),
        (
            'python_version >= "3.8" and python_version < "3.9"',
            'python_version >= "3.9" and python_version < "3.11"',
            'python_version >= "3.8" and python_version < "3.11"',
        ),
        (
            'python_version >= "3.8" and python_version < "3.9"',
            'python_version >= "3.9" and python_version < "3.10"',
            'python_version >= "3.8" and python_version < "3.10"',
        ),
        (
            'python_version == "3.8"',
            'python_version == "3.9"',
            'python_version >= "3.8" and python_version < "3.10"',
        ),
        # Ranges overlap
        (
            'python_version >= "3.6" and python_full_version <= "3.6.8"',
            'python_full_version >= "3.6.2" and python_version < "3.7"',
            'python_version == "3.6"',
        ),
        (
            'python_version >= "3.6" and python_full_version <= "3.7.8"',
            'python_full_version >= "3.6.2" and python_version < "3.8"',
            'python_version >= "3.6" and python_version < "3.8"',
        ),
        # Ranges with same end.
        (
            'python_version >= "3.6" and python_version < "3.7"',
            'python_full_version >= "3.6.2" and python_version < "3.7"',
            'python_version == "3.6"',
        ),
        (
            'python_version >= "3.6" and python_version < "3.8"',
            'python_full_version >= "3.6.2" and python_version < "3.8"',
            'python_version >= "3.6" and python_version < "3.8"',
        ),
        (
            'python_version >= "3.6" and python_version <= "3.7"',
            'python_full_version >= "3.6.2" and python_version <= "3.7"',
            'python_version >= "3.6" and python_version <= "3.7"',
        ),
        # A range covers an exact marker.
        (
            'python_version >= "3.6" and python_version <= "3.7"',
            'python_version == "3.6"',
            'python_version >= "3.6" and python_version <= "3.7"',
        ),
        (
            'python_version >= "3.6" and python_version <= "3.7"',
            'python_version == "3.6" and implementation_name == "cpython"',
            'python_version >= "3.6" and python_version <= "3.7"',
        ),
        (
            'python_version >= "3.6" and python_version <= "3.7"',
            'python_full_version == "3.6.2"',
            'python_version >= "3.6" and python_version <= "3.7"',
        ),
        (
            'python_version >= "3.6" and python_version <= "3.7"',
            'python_full_version == "3.6.2" and implementation_name == "cpython"',
            'python_version >= "3.6" and python_version <= "3.7"',
        ),
        (
            'python_version >= "3.6" and python_version <= "3.7"',
            'python_version == "3.7"',
            'python_version >= "3.6" and python_version <= "3.7"',
        ),
        (
            'python_version >= "3.6" and python_version <= "3.7"',
            'python_version == "3.7" and implementation_name == "cpython"',
            'python_version >= "3.6" and python_version <= "3.7"',
        ),
        # complex
        (
            'python_version == "3.10" and platform_system == "Linux"',
            (
                'python_version == "3.11" and platform_system != "Darwin"'
                ' or platform_system != "Linux" and platform_system != "Darwin"'
                ' and python_version <= "3.11" and python_full_version >= "3.10.0"'
            ),
            (
                'python_version >= "3.10" and python_version <= "3.11"'
                ' and platform_system != "Darwin"'
            ),
        ),
        (
            (
                'python_version == "3.6" and platform_system == "Linux"'
                ' and platform_machine == "aarch64" or python_version == "3.9"'
                ' and platform_system != "Darwin" or python_version == "3.9"'
                ' and platform_machine != "arm64" or python_version >= "3.8"'
                ' and platform_system == "Linux" and platform_machine == "aarch64"'
                ' and python_version < "3.10"'
            ),
            (
                'python_version == "3.7" and platform_system == "Linux"'
                ' and platform_machine == "aarch64"'
            ),
            (
                'python_version >= "3.6" and python_version < "3.10"'
                ' and platform_system == "Linux" and platform_machine == "aarch64"'
                ' or python_version == "3.9" and platform_machine != "arm64"'
                ' or python_version == "3.9" and platform_system != "Darwin"'
            ),
        ),
    ],
)
def test_version_ranges_collapse_on_union(
    marker1: str, marker2: str, expected: str
) -> None:
    m1 = parse_marker(marker1)
    m2 = parse_marker(marker2)
    assert str(m1.union(m2)) == expected
    assert str(m2.union(m1)) == expected


def test_multi_marker_union_with_union() -> None:
    m1 = parse_marker('sys_platform == "darwin" and implementation_name == "cpython"')
    m2 = parse_marker('python_version >= "3.6" or os_name == "Windows"')

    # Union isn't _quite_ symmetrical.
    expected1 = (
        'sys_platform == "darwin" and implementation_name == "cpython" or'
        ' python_version >= "3.6" or os_name == "Windows"'
    )
    assert str(m1.union(m2)) == expected1

    expected2 = (
        'python_version >= "3.6" or os_name == "Windows" or'
        ' sys_platform == "darwin" and implementation_name == "cpython"'
    )
    assert str(m2.union(m1)) == expected2


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
    assert m.markers == (
        parse_marker('sys_platform == "darwin"'),
        parse_marker('implementation_name == "cpython"'),
    )


def test_marker_union_deduplicate() -> None:
    m = parse_marker(
        'sys_platform == "darwin" or implementation_name == "cpython" or sys_platform'
        ' == "darwin"'
    )

    assert str(m) == 'sys_platform == "darwin" or implementation_name == "cpython"'


def test_marker_union_intersect_single_marker() -> None:
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    intersection = m.intersect(parse_marker('implementation_name == "cpython"'))
    assert (
        str(intersection) == '(sys_platform == "darwin" or python_version < "3.4")'
        ' and implementation_name == "cpython"'
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
        str(intersection) == '(sys_platform == "darwin" or python_version < "3.4") and '
        '(implementation_name == "cpython" or os_name == "Windows")'
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
        'python_version == "2.7" or python_version >= "3.4" and python_version < "4.0"'
    )
    assert str(intersection) == expected


def test_marker_union_intersect_multi_marker() -> None:
    m1 = parse_marker('sys_platform == "darwin" or python_version < "3.4"')
    m2 = parse_marker('implementation_name == "cpython" and os_name == "Windows"')

    # Intersection isn't _quite_ symmetrical.
    expected1 = (
        '(sys_platform == "darwin" or python_version < "3.4")'
        ' and implementation_name == "cpython" and os_name == "Windows"'
    )

    intersection = m1.intersect(m2)
    assert str(intersection) == expected1

    expected2 = (
        'implementation_name == "cpython" and os_name == "Windows"'
        ' and (sys_platform == "darwin" or python_version < "3.4")'
    )

    intersection = m2.intersect(m1)
    assert str(intersection) == expected2


def test_marker_union_union_with_union() -> None:
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    union = m.union(
        parse_marker('implementation_name == "cpython" or os_name == "Windows"')
    )
    assert (
        str(union) == 'sys_platform == "darwin" or python_version < "3.4" '
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
    union = MarkerUnion.of(parse_marker(""), parse_marker(""))

    assert union.is_any()


def test_marker_union_not_all_any() -> None:
    union = MarkerUnion.of(parse_marker(""), parse_marker(""), parse_marker(EMPTY))

    assert union.is_any()


def test_marker_union_all_empty() -> None:
    union = MarkerUnion.of(parse_marker(EMPTY), parse_marker(EMPTY))

    assert union.is_empty()


def test_marker_union_not_all_empty() -> None:
    union = MarkerUnion.of(parse_marker(EMPTY), parse_marker(EMPTY), parse_marker(""))

    assert not union.is_empty()


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
            (
                "platform_machine in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE"
                " amd64 AMD64 win32 WIN32'"
            ),
            {"platform_machine": "foo"},
            False,
        ),
        (
            (
                "platform_machine in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE"
                " amd64 AMD64 win32 WIN32'"
            ),
            {"platform_machine": "x86_64"},
            True,
        ),
        (
            (
                "platform_machine not in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE"
                " amd64 AMD64 win32 WIN32'"
            ),
            {"platform_machine": "foo"},
            True,
        ),
        (
            (
                "platform_machine not in 'x86_64 X86_64 aarch64 AARCH64 ppc64le PPC64LE"
                " amd64 AMD64 win32 WIN32'"
            ),
            {"platform_machine": "x86_64"},
            False,
        ),
        ('"tegra" in platform_release', {"platform_release": "5.10.120-tegra"}, True),
        ('"tegra" in platform_release', {"platform_release": "5.10.120"}, False),
        (
            '"tegra" not in platform_release',
            {"platform_release": "5.10.120-tegra"},
            False,
        ),
        ('"tegra" not in platform_release', {"platform_release": "5.10.120"}, True),
        (
            "platform_machine == 'aarch64' and 'tegra' in platform_release",
            {"platform_release": "5.10.120-tegra", "platform_machine": "aarch64"},
            True,
        ),
        (
            "platform_release != '4.9.253-tegra'",
            {"platform_release": "4.9.254-tegra"},
            True,
        ),
        (
            "platform_release != '4.9.253-tegra'",
            {"platform_release": "4.9.253"},
            True,
        ),
        (
            "platform_release >= '6.6.0+rpt-rpi-v8'",
            {"platform_release": "6.6.20+rpt-rpi-v8"},
            True,
        ),
        (
            "platform_release < '5.10.123-tegra' and platform_release >= '4.9.254-tegra'",
            {"platform_release": "4.9.254-tegra"},
            True,
        ),
        # extras
        # single extra
        ("extra == 'security'", {"extra": "quux"}, False),
        ("extra == 'security'", {"extra": "security"}, True),
        ("extra != 'security'", {"extra": "quux"}, True),
        ("extra != 'security'", {"extra": "security"}, False),
        # normalization
        ("extra == 'Security.1'", {"extra": "security-1"}, True),
        # extra unknown
        ("extra == 'a'", {}, True),
        ("extra != 'a'", {}, True),
        ("extra == 'a' and extra == 'b'", {}, True),
        # extra explicitly not set
        ("extra == 'a'", {"extra": ()}, False),
        ("extra != 'b'", {"extra": ()}, True),
        ("extra == 'a' and extra == 'b'", {"extra": ()}, False),
        ("extra == 'a' or extra == 'b'", {"extra": ()}, False),
        ("extra != 'a' and extra != 'b'", {"extra": ()}, True),
        ("extra != 'a' or extra != 'b'", {"extra": ()}, True),
        ("extra != 'a' and extra == 'b'", {"extra": ()}, False),
        ("extra != 'a' or extra == 'b'", {"extra": ()}, True),
        # multiple extras
        ("extra == 'a'", {"extra": ("a", "b")}, True),
        ("extra == 'a'", {"extra": ("b", "c")}, False),
        ("extra != 'a'", {"extra": ("a", "b")}, False),
        ("extra != 'a'", {"extra": ("b", "c")}, True),
        ("extra == 'a' and extra == 'b'", {"extra": ("a", "b", "c")}, True),
        ("extra == 'a' and extra == 'b'", {"extra": ("a", "c")}, False),
        ("extra == 'a' or extra == 'b'", {"extra": ("a", "c")}, True),
        ("extra == 'a' or extra == 'b'", {"extra": ("b", "c")}, True),
        ("extra == 'a' or extra == 'b'", {"extra": ("c", "d")}, False),
        ("extra != 'a' and extra != 'b'", {"extra": ("a", "c")}, False),
        ("extra != 'a' and extra != 'b'", {"extra": ("b", "c")}, False),
        ("extra != 'a' and extra != 'b'", {"extra": ("c", "d")}, True),
        ("extra != 'a' or extra != 'b'", {"extra": ("a", "b", "c")}, False),
        ("extra != 'a' or extra != 'b'", {"extra": ("a", "c")}, True),
        ("extra != 'a' or extra != 'b'", {"extra": ("b", "c")}, True),
        ("extra != 'a' and extra == 'b'", {"extra": ("a", "b")}, False),
        ("extra != 'a' and extra == 'b'", {"extra": ("b", "c")}, True),
        ("extra != 'a' and extra == 'b'", {"extra": ("c", "d")}, False),
        ("extra != 'a' or extra == 'b'", {"extra": ("a", "b")}, True),
        ("extra != 'a' or extra == 'b'", {"extra": ("c", "d")}, True),
        ("extra != 'a' or extra == 'b'", {"extra": ("a", "c")}, False),
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
            (
                'python_version >= "3.6" and (extra == "foo" or extra == "bar") or'
                ' implementation_name == "pypy"'
            ),
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
        (
            (
                'python_version >= "3.6" and extra == "foo" or implementation_name =='
                ' "pypy" and extra == "bar"'
            ),
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
        (
            (
                'python_version >= "3.6" or extra == "foo" and implementation_name =='
                ' "pypy" or extra == "bar"'
            ),
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
        ('extra == "foo"', ""),
        ('extra == "foo" or extra == "bar"', ""),
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
        ('python_version >= "3.6" and python_version < "3.11"', "python_version", "*"),
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
            (
                'python_version >= "3.6" and (extra == "foo" or extra == "bar") or'
                ' implementation_name == "pypy"'
            ),
            "python_version",
            'extra == "foo" or extra == "bar" or implementation_name == "pypy"',
        ),
        (
            (
                'python_version >= "3.6" and extra == "foo" or implementation_name =='
                ' "pypy" and extra == "bar"'
            ),
            "implementation_name",
            'python_version >= "3.6" and extra == "foo" or extra == "bar"',
        ),
        (
            (
                'python_version >= "3.6" or extra == "foo" and implementation_name =='
                ' "pypy" or extra == "bar"'
            ),
            "implementation_name",
            'python_version >= "3.6" or extra == "foo" or extra == "bar"',
        ),
        (
            'extra == "foo" and python_version >= "3.6" or python_version >= "3.6"',
            "extra",
            'python_version >= "3.6"',
        ),
        (
            (
                'python_version >= "2.7" and (python_version < "2.8"'
                ' or python_version >= "3.7") and python_version < "3.8"'
                ' and extra == "foo"'
            ),
            "extra",
            ('python_version == "2.7" or python_version == "3.7"'),
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
        ('python_version >= "3.6" and extra == "foo"', ["sys_platform"], ""),
        ('python_version >= "3.6" or extra == "foo"', ["sys_platform"], ""),
        ('python_version >= "3.6" or extra == "foo"', ["python_version"], ""),
        (
            'python_version >= "3.6" and (extra == "foo" or extra == "bar")',
            ["extra"],
            'extra == "foo" or extra == "bar"',
        ),
        (
            (
                'python_version >= "3.6" and (extra == "foo" or extra == "bar") or'
                ' implementation_name == "pypy"'
            ),
            ["implementation_name"],
            "",
        ),
        (
            (
                'python_version >= "3.6" and (extra == "foo" or extra == "bar") or'
                ' implementation_name == "pypy"'
            ),
            ["implementation_name", "extra"],
            'extra == "foo" or extra == "bar" or implementation_name == "pypy"',
        ),
        (
            (
                'python_version >= "3.6" and (extra == "foo" or extra == "bar") or'
                ' implementation_name == "pypy"'
            ),
            ["implementation_name", "python_version"],
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
        (
            (
                'python_version >= "3.6" and extra == "foo" or implementation_name =='
                ' "pypy" and extra == "bar"'
            ),
            ["implementation_name", "extra"],
            'extra == "foo" or implementation_name == "pypy" and extra == "bar"',
        ),
    ],
)
def test_only(marker: str, only: list[str], expected: str) -> None:
    m = parse_marker(marker)

    assert str(m.only(*only)) == expected


@pytest.mark.parametrize(
    ("marker", "constraint", "expected"),
    [
        ("", "~3.8", ""),
        ("<empty>", "~3.8", "<empty>"),
        ('sys_platform == "linux"', "~3.8", 'sys_platform == "linux"'),
        ('python_version == "3.8"', "~3.8", ""),
        ('python_version == "3.8"', ">=3.8.7,<3.9.0", ""),
        ('python_version == "3.8" or python_version >= "3.9"', ">=3.8.0,<4.0.0", ""),
        ('python_version == "3.8" or python_version >= "3.9"', ">=3.8.7,<4.0.0", ""),
        ('python_version > "3.7"', "~3.8", ""),
        ('python_version > "3.8"', "~3.8", "<empty>"),
        ('python_version >= "3.8"', "~3.8", ""),
        ('python_version >= "3.9"', "~3.8", "<empty>"),
        ('python_version == "3.9"', ">=3.9", 'python_version == "3.9"'),
        ('python_version <= "3.9"', ">=3.9", 'python_version == "3.9"'),
        ('python_version < "3.10"', ">=3.9", 'python_version == "3.9"'),
        ('python_version <= "3.10"', ">=3.9", 'python_version <= "3.10"'),
        ('python_version < "3.11"', ">=3.9", 'python_version < "3.11"'),
        ('python_full_version >= "3.8.0"', "~3.8", ""),
        ('python_full_version >= "3.8.1"', "~3.8", 'python_full_version >= "3.8.1"'),
        ('python_full_version < "3.8.0"', "~3.8", "<empty>"),
        ('python_version >= "3.8" and python_version < "3.9"', "~3.8", ""),
        ('python_version >= "3.7" and python_version < "4.0"', "~3.8", ""),
        (
            'python_full_version >= "3.8.1" and python_version < "3.9"',
            "~3.8",
            'python_full_version >= "3.8.1"',
        ),
        (
            'python_version >= "3.8" and python_full_version < "3.8.2"',
            "~3.8",
            'python_full_version < "3.8.2"',
        ),
        (
            'python_version >= "3.8" and sys_platform == "linux" and python_version < "3.9"',
            "~3.8",
            'sys_platform == "linux"',
        ),
        ('python_version < "3.8" or python_version >= "3.9"', "~3.9", ""),
        (
            'python_version < "3.8" or python_version >= "3.9"',
            ">=3.7",
            'python_version == "3.7" or python_version >= "3.9"',
        ),
        ('python_version < "3.8" or python_version >= "3.9"', "~3.7", ""),
        (
            'python_version < "3.8" or python_version >= "3.9"',
            "<=3.10",
            'python_version < "3.8" or python_version >= "3.9"',
        ),
        (
            'python_version == "3.8" or sys_platform == "linux"',
            "~3.8",
            "",
        ),
        (
            (
                'python_version < "3.8"'
                ' or python_version >= "3.9" and sys_platform == "linux"'
            ),
            "~3.9",
            'sys_platform == "linux"',
        ),
        ('python_version < "3.8" or python_version >= "3.9"', "~3.7 || ~3.9", ""),
        (
            'python_version < "3.8" or python_version >= "3.9"',
            "~3.6 || ~3.8",
            'python_version == "3.6"',
        ),
        (
            (
                'python_version < "3.8" or sys_platform == "linux"'
                ' or python_version >= "3.9"'
            ),
            "~3.7 || ~3.9",
            "",
        ),
        (
            (
                'python_version < "3.8" or sys_platform == "linux"'
                ' or python_version >= "3.9" or sys_platform == "win32"'
            ),
            "~3.7 || ~3.9",
            "",
        ),
        (
            '(python_version == "3.8" or platform_system == "Linux") and sys_platform == "darwin"',
            "~3.8",
            'sys_platform == "darwin"',
        ),
    ],
)
def test_reduce_by_python_constraint(
    marker: str, constraint: str, expected: str
) -> None:
    m = parse_marker(marker)
    c = parse_version_constraint(constraint)

    assert str(m.reduce_by_python_constraint(c)) == expected


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
            'python_full_version ~= "3.6.3"',
            'python_full_version < "3.6.3" or python_full_version >= "3.7.0"',
        ),
        ('"tegra" in platform_release', '"tegra" not in platform_release'),
        ('"tegra" not in platform_release', '"tegra" in platform_release'),
    ],
)
def test_invert(marker: str, inverse: str) -> None:
    m = parse_marker(marker)

    assert parse_marker(inverse) == m.invert()


@pytest.mark.parametrize(
    "marker, expected",
    [
        (
            (
                'python_version >= "3.6" or python_version < "3.7" or python_version <'
                ' "3.6"'
            ),
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
            "(A+B)(C+D)_",
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
        ),
        (
            "AB+AC_A(B+C)",
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
            MultiMarker(
                SingleMarker("python_version", ">=3.7"),
                MarkerUnion(
                    SingleMarker("python_version", "<3.9"),
                    SingleMarker("sys_platform", "linux"),
                ),
            ),
        ),
        (
            "A+BC_(A+B)(A+C)",
            MarkerUnion(
                SingleMarker("python_version", "<3.7"),
                MultiMarker(
                    SingleMarker("python_version", ">=3.9"),
                    SingleMarker("sys_platform", "linux"),
                ),
            ),
            MultiMarker(
                MarkerUnion(
                    SingleMarker("python_version", "<3.7"),
                    SingleMarker("python_version", ">=3.9"),
                ),
                MarkerUnion(
                    SingleMarker("python_version", "<3.7"),
                    SingleMarker("sys_platform", "linux"),
                ),
            ),
        ),
        (
            "(A+B(C+D))(E+F)_(A+B)(A+C+D)(E+F)",
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
            MultiMarker(
                MarkerUnion(
                    SingleMarker("python_version", ">=3.9"),
                    SingleMarker("implementation_name", "cpython"),
                ),
                MarkerUnion(
                    SingleMarker("python_version", ">=3.8"),
                    SingleMarker("python_version", "<3.7"),
                ),
                AtomicMarkerUnion(
                    "sys_platform",
                    UnionConstraint(
                        parse_generic_constraint("win32"),
                        parse_generic_constraint("linux"),
                    ),
                ),
            ),
        ),
        (
            "A(B+C)+(D+E)(F+G)_(A+D+E)(B+C+D+E)(A+F+G)(B+C+F+G)",
            MarkerUnion(
                MultiMarker(
                    SingleMarker("sys_platform", "!=win32"),
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
                        SingleMarker("sys_platform", "!=linux"),
                        SingleMarker("python_version", ">=3.9"),
                    ),
                ),
            ),
            MultiMarker(
                MarkerUnion(
                    SingleMarker("python_version", "<3.8"),
                    SingleMarker("python_version", ">=3.9"),
                ),
                MarkerUnion(
                    SingleMarker("python_version", "<3.7"),
                    SingleMarker("python_version", ">=3.9"),
                    SingleMarker("sys_platform", "!=linux"),
                ),
            ),
        ),
    ],
)
def test_cnf(scheme: str, marker: BaseMarker, expected: BaseMarker) -> None:
    assert cnf(marker) == expected


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
                    AtomicMarkerUnion(
                        "sys_platform",
                        UnionConstraint(
                            parse_generic_constraint("win32"),
                            parse_generic_constraint("linux"),
                        ),
                    ),
                ),
                MultiMarker(
                    SingleMarker("implementation_name", "cpython"),
                    SingleMarker("python_version", "<3.7"),
                    AtomicMarkerUnion(
                        "sys_platform",
                        UnionConstraint(
                            parse_generic_constraint("win32"),
                            parse_generic_constraint("linux"),
                        ),
                    ),
                ),
                MultiMarker(
                    SingleMarker("implementation_name", "cpython"),
                    SingleMarker("python_version", ">=3.8"),
                    AtomicMarkerUnion(
                        "sys_platform",
                        UnionConstraint(
                            parse_generic_constraint("win32"),
                            parse_generic_constraint("linux"),
                        ),
                    ),
                ),
            ),
        ),
    ],
)
def test_dnf(scheme: str, marker: BaseMarker, expected: BaseMarker) -> None:
    assert dnf(marker) == expected


def test_single_markers_are_found_in_complex_intersection() -> None:
    m1 = parse_marker('implementation_name != "pypy" and python_version <= "3.6"')
    m2 = parse_marker(
        'python_version >= "3.6" and python_version < "4.0" and implementation_name =='
        ' "cpython"'
    )
    intersection = m1.intersect(m2)
    assert (
        str(intersection)
        == 'implementation_name == "cpython" and python_version == "3.6"'
    )


@pytest.mark.parametrize(
    "marker1, marker2",
    [
        (
            (
                '(platform_system != "Windows" or platform_machine != "x86") and'
                ' python_version == "3.8"'
            ),
            'platform_system == "Windows" and platform_machine == "x86"',
        ),
        # Following example via
        # https://github.com/python-poetry/poetry-plugin-export/issues/163
        (
            (
                'python_version >= "3.8" and python_version < "3.11" and'
                ' (python_version > "3.9" or platform_system != "Windows" or'
                ' platform_machine != "x86") or python_version >= "3.11" and'
                ' python_version < "3.12"'
            ),
            (
                'python_version == "3.8" and platform_system == "Windows" and'
                ' platform_machine == "x86" or python_version == "3.9" and'
                ' platform_system == "Windows" and platform_machine == "x86"'
            ),
        ),
    ],
)
def test_empty_marker_is_found_in_complex_intersection(
    marker1: str, marker2: str
) -> None:
    m1 = parse_marker(marker1)
    m2 = parse_marker(marker2)
    assert m1.intersect(m2).is_empty()
    assert m2.intersect(m1).is_empty()


def test_empty_marker_is_found_in_complex_parse() -> None:
    marker = parse_marker(
        '(python_implementation != "pypy" or python_version != "3.6") and '
        '((python_implementation != "pypy" and python_version != "3.6") or'
        ' (python_implementation == "pypy" and python_version == "3.6")) and '
        '(python_implementation == "pypy" or python_version == "3.6")'
    )
    assert marker.is_empty()


def test_complex_union() -> None:
    """
    real world example on the way to get mutually exclusive markers
    for numpy(>=1.21.2) of https://pypi.org/project/opencv-python/4.6.0.66/
    """
    markers = [
        parse_marker(m)
        for m in [
            (
                'python_version < "3.7" and python_version >= "3.6"'
                ' and platform_system == "Darwin" and platform_machine == "arm64"'
            ),
            (
                'python_version >= "3.10" or python_version >= "3.9"'
                ' and platform_system == "Darwin" and platform_machine == "arm64"'
            ),
            (
                'python_version >= "3.8" and platform_system == "Darwin"'
                ' and platform_machine == "arm64" and python_version < "3.9"'
            ),
            (
                'python_version >= "3.7" and platform_system == "Darwin"'
                ' and platform_machine == "arm64" and python_version < "3.8"'
            ),
        ]
    ]
    assert (
        str(union(*markers))
        == 'platform_system == "Darwin" and platform_machine == "arm64"'
        ' and python_version >= "3.6" or python_version >= "3.10"'
    )


def test_complex_intersection() -> None:
    """
    inverse of real world example on the way to get mutually exclusive markers
    for numpy(>=1.21.2) of https://pypi.org/project/opencv-python/4.6.0.66/
    """
    markers = [
        parse_marker(m).invert()
        for m in [
            (
                'python_version < "3.7" and python_version >= "3.6"'
                ' and platform_system == "Darwin" and platform_machine == "arm64"'
            ),
            (
                'python_version >= "3.10" or python_version >= "3.9"'
                ' and platform_system == "Darwin" and platform_machine == "arm64"'
            ),
            (
                'python_version >= "3.8" and platform_system == "Darwin"'
                ' and platform_machine == "arm64" and python_version < "3.9"'
            ),
            (
                'python_version >= "3.7" and platform_system == "Darwin"'
                ' and platform_machine == "arm64" and python_version < "3.8"'
            ),
        ]
    ]
    assert (
        str(dnf(intersection(*markers).invert()))
        == 'platform_system == "Darwin" and platform_machine == "arm64"'
        ' and python_version >= "3.6" or python_version >= "3.10"'
    )


def test_complex_intersection_with_itertools_product_duplicates() -> None:
    """
    Real-world example from https://github.com/python-poetry/poetry/issues/10250.
    (Only occurs if the solver takes an unfortunate path.)
    Takes a long time without filtering duplicates from the itertools.product()
    in cnf/dnf early.
    """
    m1 = parse_marker(
        '(python_version > "3.9" or platform_system != "Windows"'
        ' or platform_machine != "x86") and (python_version != "3.10"'
        ' or platform_system != "Windows" or platform_python_implementation == "PyPy")'
    )
    m2 = parse_marker(
        '(platform_system != "Windows" or platform_machine != "x86"'
        ' or python_version >= "3.10" and python_version < "3.12")'
        ' and (sys_platform != "darwin" or platform_machine != "arm64")'
        ' and python_version <= "3.11" and (platform_system != "Windows"'
        ' or platform_python_implementation == "PyPy" or python_version == "3.9"'
        ' or python_version == "3.11") and python_version >= "3.9"'
        ' and (platform_system != "Windows" or platform_python_implementation == "PyPy"'
        ' or platform_machine != "x86" or python_version == "3.11")'
    )

    assert str(m1.intersect(m2)) == (
        '(python_version > "3.9" or platform_system != "Windows"'
        ' or platform_machine != "x86") and (python_version != "3.10"'
        ' or platform_system != "Windows" or platform_python_implementation == "PyPy")'
        ' and (platform_system != "Windows" or platform_machine != "x86"'
        ' or python_version >= "3.10") and python_version <= "3.11"'
        ' and (sys_platform != "darwin" or platform_machine != "arm64") and'
        ' (platform_system != "Windows" or platform_python_implementation == "PyPy"'
        ' or python_version == "3.9" or python_version == "3.11")'
        ' and python_version >= "3.9" and (platform_system != "Windows"'
        ' or platform_python_implementation == "PyPy" or platform_machine != "x86"'
        ' or python_version == "3.11")'
    )


def test_complex_union_is_deterministic() -> None:
    """
    This test might fail sporadically if marker operations are not deterministic!
    """
    m1 = parse_marker(
        'sys_platform != "darwin" and python_version >= "3.12"'
        ' and platform_system != "Emscripten" and (python_version < "4.0"'
        ' and sys_platform == "linux" and extra == "stretch"'
        ' or platform_system == "Windows" or extra == "test"'
        ' and sys_platform == "win32")'
    )
    m2 = parse_marker(
        'sys_platform == "linux" and python_version >= "3.12"'
        ' and platform_system == "Emscripten" and python_version < "4.0"'
        ' and extra == "stretch" or sys_platform == "win32"'
        ' and python_version >= "3.12" and platform_system == "Emscripten"'
        ' and extra == "test"'
    )
    assert str(m1.union(m2)) == (
        'python_version >= "3.12" and platform_system == "Windows"'
        ' and sys_platform != "darwin" or sys_platform == "linux"'
        ' and python_version >= "3.12" and python_version < "4.0"'
        ' and extra == "stretch" or sys_platform == "win32"'
        ' and python_version >= "3.12" and extra == "test" or (sys_platform == "linux"'
        ' or sys_platform == "win32") and python_version >= "3.12"'
        ' and extra == "stretch" and extra == "test" and python_version < "4.0"'
    )


def test_union_avoids_combinatorial_explosion() -> None:
    """
    combinatorial explosion without AtomicMultiMarker and AtomicMarkerUnion
    based gevent constraint of sqlalchemy 2.0.7
    see https://github.com/python-poetry/poetry/issues/7689 for details
    """
    expected = (
        'python_full_version >= "3.11.0" and python_version < "4.0"'
        ' and (platform_machine == "aarch64" or platform_machine == "ppc64le"'
        ' or platform_machine == "x86_64" or platform_machine == "amd64"'
        ' or platform_machine == "AMD64" or platform_machine == "win32"'
        ' or platform_machine == "WIN32")'
    )
    m1 = parse_marker(expected)
    m2 = parse_marker(
        'python_full_version >= "3.11.0" and python_full_version < "4.0.0"'
        ' and (platform_machine == "aarch64" or platform_machine == "ppc64le"'
        ' or platform_machine == "x86_64" or platform_machine == "amd64"'
        ' or platform_machine == "AMD64" or platform_machine == "win32"'
        ' or platform_machine == "WIN32")'
    )
    assert str(m1.union(m2)) == expected
    assert str(m2.union(m1)) == expected


def test_intersection_avoids_combinatorial_explosion() -> None:
    """
    combinatorial explosion without AtomicMultiMarker and AtomicMarkerUnion
    based gevent constraint of sqlalchemy 2.0.7
    see https://github.com/python-poetry/poetry/issues/7689 for details
    """
    m1 = parse_marker(
        'python_full_version >= "3.11.0" and python_full_version < "4.0.0"'
    )
    m2 = parse_marker(
        'python_version >= "3" and (platform_machine == "aarch64" '
        'or platform_machine == "ppc64le" or platform_machine == "x86_64" '
        'or platform_machine == "amd64" or platform_machine == "AMD64" '
        'or platform_machine == "win32" or platform_machine == "WIN32")'
    )
    assert (
        str(m1.intersect(m2))
        == 'python_version >= "3.11" and python_full_version < "4.0.0"'
        ' and (platform_machine == "aarch64" or platform_machine == "ppc64le"'
        ' or platform_machine == "x86_64" or platform_machine == "amd64"'
        ' or platform_machine == "AMD64" or platform_machine == "win32"'
        ' or platform_machine == "WIN32")'
    )
    assert (
        str(m2.intersect(m1)) == 'python_version >= "3.11"'
        ' and (platform_machine == "aarch64" or platform_machine == "ppc64le"'
        ' or platform_machine == "x86_64" or platform_machine == "amd64"'
        ' or platform_machine == "AMD64" or platform_machine == "win32"'
        ' or platform_machine == "WIN32") and python_full_version < "4.0.0"'
    )


@pytest.mark.parametrize(
    ("marker1", "marker2", "expected"),
    [
        (
            (
                '(python_version < "3.9" or extra != "bigquery" and extra != "parquet"'
                ' and extra != "motherduck" and extra != "athena"'
                ' and extra != "synapse" and extra != "clickhouse"'
                ' and extra != "dremio" and extra != "lancedb"'
                ' and extra != "deltalake" and extra != "pyiceberg"'
                ' and python_version < "3.13") and extra != "postgres"'
                ' and extra != "redshift" and extra != "postgis"'
            ),
            (
                'python_version >= "3.12" and python_version < "3.13"'
                ' or extra != "databricks"'
            ),
            (
                '(python_version < "3.9" or extra != "bigquery" and extra != "parquet"'
                ' and extra != "motherduck" and extra != "athena"'
                ' and extra != "synapse" and extra != "clickhouse"'
                ' and extra != "dremio" and extra != "lancedb"'
                ' and extra != "deltalake" and extra != "pyiceberg")'
                ' and python_version < "3.13" and extra != "postgres"'
                ' and extra != "redshift" and extra != "postgis"'
                ' and (python_version == "3.12" or extra != "databricks")'
            ),
        ),
        (
            (
                'python_version < "3.7" and (python_version < "3.6"'
                ' or platform_system != "Darwin" or platform_machine != "arm64")'
            ),
            (
                '(python_version < "3.6" or platform_system != "Linux"'
                ' or platform_machine != "aarch64") and python_version < "3.9"'
            ),
            (
                'python_version < "3.7" and (python_version < "3.6"'
                ' or platform_system != "Darwin" or platform_machine != "arm64")'
                ' and (python_version < "3.6" or platform_system != "Linux"'
                ' or platform_machine != "aarch64")'
            ),
        ),
    ],
)
def test_intersection_no_endless_recursion(
    marker1: str, marker2: str, expected: str
) -> None:
    assert str(parse_marker(marker1).intersect(parse_marker(marker2))) == expected


@pytest.mark.parametrize(
    "python_version, python_full_version, "
    "expected_intersection_version, expected_union_version",
    [
        # python_version > 3.6 (equal to python_full_version >= 3.7.0)
        ('> "3.6"', '> "3.5.2"', '> "3.6"', '> "3.5.2"'),
        ('> "3.6"', '>= "3.5.2"', '> "3.6"', '>= "3.5.2"'),
        ('> "3.6"', '> "3.6.2"', '> "3.6"', '> "3.6.2"'),
        ('> "3.6"', '>= "3.6.2"', '> "3.6"', '>= "3.6.2"'),
        ('> "3.6"', '> "3.7.0"', '> "3.7.0"', '> "3.6"'),
        ('> "3.6"', '>= "3.7.0"', '> "3.6"', '> "3.6"'),
        ('> "3.6"', '> "3.7.1"', '> "3.7.1"', '> "3.6"'),
        ('> "3.6"', '>= "3.7.1"', '>= "3.7.1"', '> "3.6"'),
        ('> "3.6"', '== "3.6.2"', EMPTY, None),
        ('> "3.6"', '== "3.7.0"', '== "3.7.0"', '> "3.6"'),
        ('> "3.6"', '== "3.7.1"', '== "3.7.1"', '> "3.6"'),
        ('> "3.6"', '!= "3.6.2"', '> "3.6"', '!= "3.6.2"'),
        ('> "3.6"', '!= "3.7.0"', '> "3.7.0"', ""),
        ('> "3.6"', '!= "3.7.1"', None, ""),
        ('> "3.6"', '< "3.7.0"', EMPTY, ""),
        ('> "3.6"', '<= "3.7.0"', '== "3.7.0"', ""),
        ('> "3.6"', '< "3.7.1"', None, ""),
        ('> "3.6"', '<= "3.7.1"', None, ""),
        # python_version >= 3.6 (equal to python_full_version >= 3.6.0)
        ('>= "3.6"', '> "3.5.2"', '>= "3.6"', '> "3.5.2"'),
        ('>= "3.6"', '>= "3.5.2"', '>= "3.6"', '>= "3.5.2"'),
        ('>= "3.6"', '> "3.6.0"', '> "3.6.0"', '>= "3.6"'),
        ('>= "3.6"', '>= "3.6.0"', '>= "3.6"', '>= "3.6"'),
        ('>= "3.6"', '> "3.6.1"', '> "3.6.1"', '>= "3.6"'),
        ('>= "3.6"', '>= "3.6.1"', '>= "3.6.1"', '>= "3.6"'),
        ('>= "3.6"', '== "3.5.2"', EMPTY, None),
        ('>= "3.6"', '== "3.6.0"', '== "3.6.0"', '>= "3.6"'),
        ('>= "3.6"', '!= "3.5.2"', '>= "3.6"', '!= "3.5.2"'),
        ('>= "3.6"', '!= "3.6.0"', '> "3.6.0"', ""),
        ('>= "3.6"', '!= "3.6.1"', None, ""),
        ('>= "3.6"', '!= "3.7.1"', None, ""),
        ('>= "3.6"', '< "3.6.0"', EMPTY, ""),
        ('>= "3.6"', '<= "3.6.0"', '== "3.6.0"', ""),
        ('>= "3.6"', '< "3.6.1"', None, ""),  # '== "3.6.0"'
        ('>= "3.6"', '<= "3.6.1"', None, ""),
        # python_version < 3.6 (equal to python_full_version < 3.6.0)
        ('< "3.6"', '< "3.5.2"', '< "3.5.2"', '< "3.6"'),
        ('< "3.6"', '<= "3.5.2"', '<= "3.5.2"', '< "3.6"'),
        ('< "3.6"', '< "3.6.0"', '< "3.6"', '< "3.6"'),
        ('< "3.6"', '<= "3.6.0"', '< "3.6"', '<= "3.6.0"'),
        ('< "3.6"', '< "3.6.1"', '< "3.6"', '< "3.6.1"'),
        ('< "3.6"', '<= "3.6.1"', '< "3.6"', '<= "3.6.1"'),
        ('< "3.6"', '== "3.5.2"', '== "3.5.2"', '< "3.6"'),
        ('< "3.6"', '== "3.6.0"', EMPTY, '<= "3.6.0"'),
        ('< "3.6"', '!= "3.5.2"', None, ""),
        ('< "3.6"', '!= "3.6.0"', '< "3.6"', '!= "3.6.0"'),
        ('< "3.6"', '> "3.6.0"', EMPTY, '!= "3.6.0"'),
        ('< "3.6"', '>= "3.6.0"', EMPTY, ""),
        ('< "3.6"', '> "3.5.2"', None, ""),
        ('< "3.6"', '>= "3.5.2"', None, ""),
        # python_version <= 3.6 (equal to python_full_version < 3.7.0)
        ('<= "3.6"', '< "3.6.1"', '< "3.6.1"', '<= "3.6"'),
        ('<= "3.6"', '<= "3.6.1"', '<= "3.6.1"', '<= "3.6"'),
        ('<= "3.6"', '< "3.7.0"', '<= "3.6"', '<= "3.6"'),
        ('<= "3.6"', '<= "3.7.0"', '<= "3.6"', '<= "3.7.0"'),
        ('<= "3.6"', '== "3.6.1"', '== "3.6.1"', '<= "3.6"'),
        ('<= "3.6"', '== "3.7.0"', EMPTY, '<= "3.7.0"'),
        ('<= "3.6"', '!= "3.6.1"', None, ""),
        ('<= "3.6"', '!= "3.7.0"', '<= "3.6"', '!= "3.7.0"'),
        ('<= "3.6"', '> "3.7.0"', EMPTY, '!= "3.7.0"'),
        ('<= "3.6"', '>= "3.7.0"', EMPTY, ""),
        ('<= "3.6"', '> "3.6.2"', None, ""),
        ('<= "3.6"', '>= "3.6.2"', None, ""),
        # python_version == 3.6  # noqa: ERA001
        # (equal to python_full_version >= 3.6.0 and python_full_version < 3.7.0)
        ('== "3.6"', '< "3.5.2"', EMPTY, None),
        ('== "3.6"', '<= "3.5.2"', EMPTY, None),
        ('== "3.6"', '> "3.5.2"', '== "3.6"', '> "3.5.2"'),
        ('== "3.6"', '>= "3.5.2"', '== "3.6"', '>= "3.5.2"'),
        ('== "3.6"', '!= "3.5.2"', '== "3.6"', '!= "3.5.2"'),
        ('== "3.6"', '< "3.6.0"', EMPTY, '< "3.7"'),
        ('== "3.6"', '<= "3.6.0"', '== "3.6.0"', '< "3.7"'),
        ('== "3.6"', '> "3.6.0"', None, '>= "3.6"'),
        ('== "3.6"', '>= "3.6.0"', '== "3.6"', '>= "3.6"'),
        ('== "3.6"', '!= "3.6.0"', None, ""),
        ('== "3.6"', '< "3.6.1"', None, '< "3.7"'),
        ('== "3.6"', '<= "3.6.1"', None, '< "3.7"'),
        ('== "3.6"', '> "3.6.1"', None, '>= "3.6"'),
        ('== "3.6"', '>= "3.6.1"', None, '>= "3.6"'),
        ('== "3.6"', '!= "3.6.1"', None, ""),
        ('== "3.6"', '< "3.7.0"', '== "3.6"', '< "3.7"'),
        ('== "3.6"', '<= "3.7.0"', '== "3.6"', '<= "3.7.0"'),
        ('== "3.6"', '> "3.7.0"', EMPTY, None),
        ('== "3.6"', '>= "3.7.0"', EMPTY, '>= "3.6"'),
        ('== "3.6"', '!= "3.7.0"', '== "3.6"', '!= "3.7.0"'),
        ('== "3.6"', '<= "3.7.1"', '== "3.6"', '<= "3.7.1"'),
        ('== "3.6"', '< "3.7.1"', '== "3.6"', '< "3.7.1"'),
        ('== "3.6"', '> "3.7.1"', EMPTY, None),
        ('== "3.6"', '>= "3.7.1"', EMPTY, None),
        ('== "3.6"', '!= "3.7.1"', '== "3.6"', '!= "3.7.1"'),
        # python_version != 3.6  # noqa: ERA001
        # (equal to python_full_version < 3.6.0 or python_full_version >= 3.7.0)
        ('!= "3.6"', '< "3.5.2"', '< "3.5.2"', '!= "3.6"'),
        ('!= "3.6"', '<= "3.5.2"', '<= "3.5.2"', '!= "3.6"'),
        ('!= "3.6"', '> "3.5.2"', None, ""),
        ('!= "3.6"', '>= "3.5.2"', None, ""),
        ('!= "3.6"', '!= "3.5.2"', None, ""),
        ('!= "3.6"', '< "3.6.0"', '< "3.6"', '!= "3.6"'),
        ('!= "3.6"', '<= "3.6.0"', '< "3.6"', None),
        ('!= "3.6"', '> "3.6.0"', '>= "3.7"', '!= "3.6.0"'),
        ('!= "3.6"', '>= "3.6.0"', '>= "3.7"', ""),
        ('!= "3.6"', '!= "3.6.0"', '!= "3.6"', '!= "3.6.0"'),
        ('!= "3.6"', '< "3.6.1"', '< "3.6"', None),
        ('!= "3.6"', '<= "3.6.1"', '< "3.6"', None),
        ('!= "3.6"', '> "3.6.1"', '>= "3.7"', None),
        ('!= "3.6"', '>= "3.6.1"', '>= "3.7"', None),
        ('!= "3.6"', '!= "3.6.1"', '!= "3.6"', '!= "3.6.1"'),
        ('!= "3.6"', '< "3.7.0"', '< "3.6"', ""),
        ('!= "3.6"', '<= "3.7.0"', None, ""),
        ('!= "3.6"', '> "3.7.0"', '> "3.7.0"', '!= "3.6"'),
        ('!= "3.6"', '>= "3.7.0"', '>= "3.7"', '!= "3.6"'),
        ('!= "3.6"', '!= "3.7.0"', None, ""),
        ('!= "3.6"', '<= "3.7.1"', None, ""),
        ('!= "3.6"', '< "3.7.1"', None, ""),
        ('!= "3.6"', '> "3.7.1"', '> "3.7.1"', '!= "3.6"'),
        ('!= "3.6"', '>= "3.7.1"', '>= "3.7.1"', '!= "3.6"'),
        ('!= "3.6"', '!= "3.7.1"', None, ""),
    ],
)
def test_merging_python_version_and_python_full_version(
    python_version: str,
    python_full_version: str,
    expected_intersection_version: str,
    expected_union_version: str,
) -> None:
    m = f"python_version {python_version}"
    m2 = f"python_full_version {python_full_version}"

    def get_expected_marker(expected_version: str, op: str) -> str:
        if expected_version is None:
            expected = f"{m} {op} {m2}"
        elif expected_version in ("", EMPTY):
            expected = expected_version
        else:
            expected_marker_name = (
                "python_version"
                if expected_version.count(".") < 2
                else "python_full_version"
            )
            expected = f"{expected_marker_name} {expected_version}"
        return expected

    expected_intersection = get_expected_marker(expected_intersection_version, "and")
    expected_union = get_expected_marker(expected_union_version, "or")

    intersection = parse_marker(m).intersect(parse_marker(m2))
    assert str(intersection) == expected_intersection

    union = parse_marker(m).union(parse_marker(m2))
    assert str(union) == expected_union
