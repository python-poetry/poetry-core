import os

import pytest

from poetry.core.version.markers import MarkerUnion
from poetry.core.version.markers import MultiMarker
from poetry.core.version.markers import SingleMarker
from poetry.core.version.markers import parse_marker


def test_single_marker():
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


def test_single_marker_intersect():
    m = parse_marker('sys_platform == "darwin"')

    intersection = m.intersect(parse_marker('implementation_name == "cpython"'))
    assert (
        str(intersection)
        == 'sys_platform == "darwin" and implementation_name == "cpython"'
    )

    m = parse_marker('python_version >= "3.4"')

    intersection = m.intersect(parse_marker('python_version < "3.6"'))
    assert str(intersection) == 'python_version >= "3.4" and python_version < "3.6"'


def test_single_marker_intersect_compacts_constraints():
    m = parse_marker('python_version < "3.6"')

    intersection = m.intersect(parse_marker('python_version < "3.4"'))
    assert str(intersection) == 'python_version < "3.4"'


def test_single_marker_intersect_with_multi():
    m = parse_marker('sys_platform == "darwin"')

    intersection = m.intersect(
        parse_marker('implementation_name == "cpython" and python_version >= "3.6"')
    )
    assert (
        str(intersection)
        == 'implementation_name == "cpython" and python_version >= "3.6" and sys_platform == "darwin"'
    )


def test_single_marker_intersect_with_multi_with_duplicate():
    m = parse_marker('python_version < "4.0"')

    intersection = m.intersect(
        parse_marker('sys_platform == "darwin" and python_version < "4.0"')
    )
    assert str(intersection) == 'sys_platform == "darwin" and python_version < "4.0"'


def test_single_marker_intersect_with_multi_compacts_constraint():
    m = parse_marker('python_version < "3.6"')

    intersection = m.intersect(
        parse_marker('implementation_name == "cpython" and python_version < "3.4"')
    )
    assert (
        str(intersection)
        == 'implementation_name == "cpython" and python_version < "3.4"'
    )


def test_single_marker_not_in_python_intersection():
    m = parse_marker('python_version not in "2.7, 3.0, 3.1"')

    intersection = m.intersect(
        parse_marker('python_version not in "2.7, 3.0, 3.1, 3.2"')
    )
    assert str(intersection) == 'python_version not in "2.7, 3.0, 3.1, 3.2"'


def test_single_marker_union():
    m = parse_marker('sys_platform == "darwin"')

    intersection = m.union(parse_marker('implementation_name == "cpython"'))
    assert (
        str(intersection)
        == 'sys_platform == "darwin" or implementation_name == "cpython"'
    )

    m = parse_marker('python_version >= "3.4"')

    intersection = m.union(parse_marker('python_version < "3.6"'))
    assert str(intersection) == 'python_version >= "3.4" or python_version < "3.6"'


def test_single_marker_union_compacts_constraints():
    m = parse_marker('python_version < "3.6"')

    union = m.union(parse_marker('python_version < "3.4"'))
    assert str(union) == 'python_version < "3.6"'


def test_single_marker_union_with_multi():
    m = parse_marker('sys_platform == "darwin"')

    union = m.union(
        parse_marker('implementation_name == "cpython" and python_version >= "3.6"')
    )
    assert (
        str(union)
        == 'implementation_name == "cpython" and python_version >= "3.6" or sys_platform == "darwin"'
    )


def test_single_marker_union_with_multi_duplicate():
    m = parse_marker('sys_platform == "darwin" and python_version >= "3.6"')

    union = m.union(
        parse_marker('sys_platform == "darwin" and python_version >= "3.6"')
    )
    assert str(union) == 'sys_platform == "darwin" and python_version >= "3.6"'


def test_single_marker_union_with_union():
    m = parse_marker('sys_platform == "darwin"')

    union = m.union(
        parse_marker('implementation_name == "cpython" or python_version >= "3.6"')
    )
    assert (
        str(union)
        == 'implementation_name == "cpython" or python_version >= "3.6" or sys_platform == "darwin"'
    )


def test_single_marker_not_in_python_union():
    m = parse_marker('python_version not in "2.7, 3.0, 3.1"')

    union = m.union(parse_marker('python_version not in "2.7, 3.0, 3.1, 3.2"'))
    assert str(union) == 'python_version not in "2.7, 3.0, 3.1"'


def test_single_marker_union_with_union_duplicate():
    m = parse_marker('sys_platform == "darwin"')

    union = m.union(parse_marker('sys_platform == "darwin" or python_version >= "3.6"'))
    assert str(union) == 'sys_platform == "darwin" or python_version >= "3.6"'

    m = parse_marker('python_version >= "3.7"')

    union = m.union(parse_marker('sys_platform == "darwin" or python_version >= "3.6"'))
    assert str(union) == 'sys_platform == "darwin" or python_version >= "3.6"'

    m = parse_marker('python_version <= "3.6"')

    union = m.union(parse_marker('sys_platform == "darwin" or python_version < "3.4"'))
    assert str(union) == 'sys_platform == "darwin" or python_version <= "3.6"'


def test_multi_marker():
    m = parse_marker('sys_platform == "darwin" and implementation_name == "cpython"')

    assert isinstance(m, MultiMarker)
    assert m.markers == [
        parse_marker('sys_platform == "darwin"'),
        parse_marker('implementation_name == "cpython"'),
    ]


def test_multi_marker_is_empty_is_contradictory():
    m = parse_marker(
        'sys_platform == "linux" and python_version >= "3.5" and python_version < "2.8"'
    )

    assert m.is_empty()

    m = parse_marker('sys_platform == "linux" and sys_platform == "win32"')

    assert m.is_empty()


def test_multi_marker_intersect_multi():
    m = parse_marker('sys_platform == "darwin" and implementation_name == "cpython"')

    intersection = m.intersect(
        parse_marker('python_version >= "3.6" and os_name == "Windows"')
    )
    assert str(intersection) == (
        'sys_platform == "darwin" and implementation_name == "cpython" '
        'and python_version >= "3.6" and os_name == "Windows"'
    )


def test_multi_marker_intersect_multi_with_overlapping_constraints():
    m = parse_marker('sys_platform == "darwin" and python_version < "3.6"')

    intersection = m.intersect(
        parse_marker(
            'python_version <= "3.4" and os_name == "Windows" and sys_platform == "darwin"'
        )
    )
    assert str(intersection) == (
        'sys_platform == "darwin" and python_version <= "3.4" and os_name == "Windows"'
    )


def test_multi_marker_union_multi():
    m = parse_marker('sys_platform == "darwin" and implementation_name == "cpython"')

    intersection = m.union(
        parse_marker('python_version >= "3.6" and os_name == "Windows"')
    )
    assert str(intersection) == (
        'sys_platform == "darwin" and implementation_name == "cpython" '
        'or python_version >= "3.6" and os_name == "Windows"'
    )


def test_multi_marker_union_with_union():
    m = parse_marker('sys_platform == "darwin" and implementation_name == "cpython"')

    intersection = m.union(
        parse_marker('python_version >= "3.6" or os_name == "Windows"')
    )
    assert str(intersection) == (
        'python_version >= "3.6" or os_name == "Windows"'
        ' or sys_platform == "darwin" and implementation_name == "cpython"'
    )


def test_marker_union():
    m = parse_marker('sys_platform == "darwin" or implementation_name == "cpython"')

    assert isinstance(m, MarkerUnion)
    assert m.markers == [
        parse_marker('sys_platform == "darwin"'),
        parse_marker('implementation_name == "cpython"'),
    ]


def test_marker_union_deduplicate():
    m = parse_marker(
        'sys_platform == "darwin" or implementation_name == "cpython" or sys_platform == "darwin"'
    )

    assert str(m) == 'sys_platform == "darwin" or implementation_name == "cpython"'


def test_marker_union_intersect_single_marker():
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    intersection = m.intersect(parse_marker('implementation_name == "cpython"'))
    assert str(intersection) == (
        'sys_platform == "darwin" and implementation_name == "cpython" '
        'or python_version < "3.4" and implementation_name == "cpython"'
    )


def test_marker_union_intersect_single_with_overlapping_constraints():
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    intersection = m.intersect(parse_marker('python_version <= "3.6"'))
    assert (
        str(intersection)
        == 'sys_platform == "darwin" and python_version <= "3.6" or python_version < "3.4"'
    )

    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')
    intersection = m.intersect(parse_marker('sys_platform == "darwin"'))
    assert (
        str(intersection)
        == 'sys_platform == "darwin" or python_version < "3.4" and sys_platform == "darwin"'
    )


def test_marker_union_intersect_marker_union():
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    intersection = m.intersect(
        parse_marker('implementation_name == "cpython" or os_name == "Windows"')
    )
    assert str(intersection) == (
        'sys_platform == "darwin" and implementation_name == "cpython" '
        'or sys_platform == "darwin" and os_name == "Windows" or '
        'python_version < "3.4" and implementation_name == "cpython" or '
        'python_version < "3.4" and os_name == "Windows"'
    )


def test_marker_union_intersect_marker_union_drops_unnecessary_markers():
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
    assert expected == str(intersection)


def test_marker_union_intersect_multi_marker():
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    intersection = m.intersect(
        parse_marker('implementation_name == "cpython" and os_name == "Windows"')
    )
    assert str(intersection) == (
        'implementation_name == "cpython" and os_name == "Windows" and sys_platform == "darwin" '
        'or implementation_name == "cpython" and os_name == "Windows" and python_version < "3.4"'
    )


def test_marker_union_union_with_union():
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    union = m.union(
        parse_marker('implementation_name == "cpython" or os_name == "Windows"')
    )
    assert str(union) == (
        'sys_platform == "darwin" or python_version < "3.4" '
        'or implementation_name == "cpython" or os_name == "Windows"'
    )


def test_marker_union_union_duplicates():
    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    union = m.union(parse_marker('sys_platform == "darwin" or os_name == "Windows"'))
    assert str(union) == (
        'sys_platform == "darwin" or python_version < "3.4" or os_name == "Windows"'
    )

    m = parse_marker('sys_platform == "darwin" or python_version < "3.4"')

    union = m.union(
        parse_marker(
            'sys_platform == "darwin" or os_name == "Windows" or python_version <= "3.6"'
        )
    )
    assert str(union) == (
        'sys_platform == "darwin" or python_version <= "3.6" or os_name == "Windows"'
    )


def test_marker_union_all_any():
    union = MarkerUnion(parse_marker(""), parse_marker(""))

    assert union.is_any()


def test_marker_union_not_all_any():
    union = MarkerUnion(parse_marker(""), parse_marker(""), parse_marker("<empty>"))

    assert union.is_any()


def test_marker_union_all_empty():
    union = MarkerUnion(parse_marker("<empty>"), parse_marker("<empty>"))

    assert union.is_empty()


def test_marker_union_not_all_empty():
    union = MarkerUnion(
        parse_marker("<empty>"), parse_marker("<empty>"), parse_marker("")
    )

    assert not union.is_empty()


def test_marker_str_conversion_skips_empty_and_any():
    union = MarkerUnion(
        parse_marker("<empty>"),
        parse_marker(
            'sys_platform == "darwin" or python_version <= "3.6" or os_name == "Windows"'
        ),
        parse_marker(""),
    )

    assert str(union) == (
        'sys_platform == "darwin" or python_version <= "3.6" or os_name == "Windows"'
    )


def test_intersect_compacts_constraints():
    m = parse_marker('python_version < "4.0"')

    intersection = m.intersect(parse_marker('python_version < "5.0"'))
    assert str(intersection) == 'python_version < "4.0"'


def test_multi_marker_removes_duplicates():
    m = parse_marker('sys_platform == "win32" and sys_platform == "win32"')

    assert 'sys_platform == "win32"' == str(m)

    m = parse_marker(
        'sys_platform == "darwin" and implementation_name == "cpython" '
        'and sys_platform == "darwin" and implementation_name == "cpython"'
    )

    assert 'sys_platform == "darwin" and implementation_name == "cpython"' == str(m)


@pytest.mark.parametrize(
    ("marker_string", "environment", "expected"),
    [
        ("os_name == '{0}'".format(os.name), None, True),
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
            "python_version ~= '2.7.0' and (os_name == 'foo' or " "os_name == 'bar')",
            {"os_name": "foo", "python_version": "2.7.4"},
            True,
        ),
        (
            "python_version ~= '2.7.0' and (os_name == 'foo' or " "os_name == 'bar')",
            {"os_name": "bar", "python_version": "2.7.4"},
            True,
        ),
        (
            "python_version ~= '2.7.0' and (os_name == 'foo' or " "os_name == 'bar')",
            {"os_name": "other", "python_version": "2.7.4"},
            False,
        ),
        ("extra == 'security'", {"extra": "quux"}, False),
        ("extra == 'security'", {"extra": "security"}, True),
        ("os.name == '{0}'".format(os.name), None, True),
        ("sys.platform == 'win32'", {"sys_platform": "linux2"}, False),
        ("platform.version in 'Ubuntu'", {"platform_version": "#39"}, False),
        ("platform.machine=='x86_64'", {"platform_machine": "x86_64"}, True),
        (
            "platform.python_implementation=='Jython'",
            {"platform_python_implementation": "CPython"},
            False,
        ),
        (
            "python_version == '2.5' and platform.python_implementation" "!= 'Jython'",
            {"python_version": "2.7"},
            False,
        ),
    ],
)
def test_validate(marker_string, environment, expected):
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
def test_parse_version_like_markers(marker, env):
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
            'python_version >= "3.6" and (extra == "foo" or extra == "bar") or implementation_name == "pypy"',
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
        (
            'python_version >= "3.6" and extra == "foo" or implementation_name == "pypy" and extra == "bar"',
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
        (
            'python_version >= "3.6" or extra == "foo" and implementation_name == "pypy" or extra == "bar"',
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
    ],
)
def test_without_extras(marker, expected):
    m = parse_marker(marker)

    assert expected == str(m.without_extras())


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
            '(extra == "foo" or extra == "bar")',
        ),
        (
            'python_version >= "3.6" and (extra == "foo" or extra == "bar") or implementation_name == "pypy"',
            "python_version",
            '(extra == "foo" or extra == "bar") or implementation_name == "pypy"',
        ),
        (
            'python_version >= "3.6" and extra == "foo" or implementation_name == "pypy" and extra == "bar"',
            "implementation_name",
            'python_version >= "3.6" and extra == "foo" or extra == "bar"',
        ),
        (
            'python_version >= "3.6" or extra == "foo" and implementation_name == "pypy" or extra == "bar"',
            "implementation_name",
            'python_version >= "3.6" or extra == "foo" or extra == "bar"',
        ),
    ],
)
def test_exclude(marker, excluded, expected):
    m = parse_marker(marker)

    if expected == "*":
        assert m.exclude(excluded).is_any()
    else:
        assert expected == str(m.exclude(excluded))


@pytest.mark.parametrize(
    "marker, only, expected",
    [
        ('python_version >= "3.6"', ["python_version"], 'python_version >= "3.6"'),
        (
            'python_version >= "3.6" and extra == "foo"',
            ["python_version"],
            'python_version >= "3.6"',
        ),
        (
            'python_version >= "3.6" and (extra == "foo" or extra == "bar")',
            ["extra"],
            '(extra == "foo" or extra == "bar")',
        ),
        (
            'python_version >= "3.6" and (extra == "foo" or extra == "bar") or implementation_name == "pypy"',
            ["implementation_name"],
            'implementation_name == "pypy"',
        ),
        (
            'python_version >= "3.6" and extra == "foo" or implementation_name == "pypy" and extra == "bar"',
            ["implementation_name"],
            'implementation_name == "pypy"',
        ),
        (
            'python_version >= "3.6" or extra == "foo" and implementation_name == "pypy" or extra == "bar"',
            ["implementation_name"],
            'implementation_name == "pypy"',
        ),
        (
            'python_version >= "3.6" or extra == "foo" and implementation_name == "pypy" or extra == "bar"',
            ["implementation_name", "python_version"],
            'python_version >= "3.6" or implementation_name == "pypy"',
        ),
    ],
)
def test_only(marker, only, expected):
    m = parse_marker(marker)

    assert expected == str(m.only(*only))


def test_union_of_a_single_marker_is_the_single_marker():
    union = MarkerUnion.of(SingleMarker("python_version", ">= 2.7"))

    assert SingleMarker("python_version", ">= 2.7") == union


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
def test_invert(marker, inverse):
    m = parse_marker(marker)

    assert parse_marker(inverse) == m.invert()


@pytest.mark.parametrize(
    "marker, expected",
    [
        (
            'python_version >= "3.6" or python_version < "3.7" or python_version < "3.6"',
            'python_version >= "3.6" or python_version < "3.7"',
        ),
    ],
)
def test_union_should_drop_markers_if_their_complement_is_present(marker, expected):
    m = parse_marker(marker)

    assert parse_marker(expected) == m
