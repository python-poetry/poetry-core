from __future__ import annotations

import re

from typing import Any

import pytest

from poetry.core.semver.helpers import parse_constraint
from poetry.core.version.requirements import InvalidRequirement
from poetry.core.version.requirements import Requirement


def assert_requirement(
    req: Requirement,
    name: str,
    url: str | None = None,
    extras: list[str] | None = None,
    constraint: str = "*",
    marker: str | None = None,
) -> None:
    if extras is None:
        extras = []

    assert name == req.name
    assert url == req.url
    assert sorted(extras) == sorted(req.extras)
    assert parse_constraint(constraint) == req.constraint

    if marker:
        assert marker == str(req.marker)


@pytest.mark.parametrize(
    ["string", "expected"],
    [
        ("A", {"name": "A"}),
        ("aa", {"name": "aa"}),
        ("name", {"name": "name"}),
        ("foo-bar.quux_baz", {"name": "foo-bar.quux_baz"}),
        ("name>=3", {"name": "name", "constraint": ">=3"}),
        ("name>=3.*", {"name": "name", "constraint": ">=3.0"}),
        ("name<3.*", {"name": "name", "constraint": "<3.0"}),
        ("name>3.5.*", {"name": "name", "constraint": ">3.5"}),
        ("name==1.0.post1", {"name": "name", "constraint": "==1.0.post1"}),
        ("name==1.2.0b1.dev0", {"name": "name", "constraint": "==1.2.0b1.dev0"}),
        (
            "name>=1.2.3;python_version=='2.6'",
            {
                "name": "name",
                "constraint": ">=1.2.3",
                "marker": 'python_version == "2.6"',
            },
        ),
        ("name (==4)", {"name": "name", "constraint": "==4"}),
        ("name>=2,<3", {"name": "name", "constraint": ">=2,<3"}),
        ("name >=2, <3", {"name": "name", "constraint": ">=2,<3"}),
        # PEP 440: https://www.python.org/dev/peps/pep-0440/#compatible-release
        ("name (~=3.2)", {"name": "name", "constraint": ">=3.2.0,<4.0"}),
        ("name (~=3.2.1)", {"name": "name", "constraint": ">=3.2.1,<3.3.0"}),
        # Extras
        ("foobar [quux,bar]", {"name": "foobar", "extras": ["quux", "bar"]}),
        ("foo[]", {"name": "foo"}),
        # Url
        ("foo @ http://example.com", {"name": "foo", "url": "http://example.com"}),
        (
            'foo @ http://example.com ; os_name=="a"',
            {"name": "foo", "url": "http://example.com", "marker": 'os_name == "a"'},
        ),
        (
            "name @ file:///absolute/path",
            {"name": "name", "url": "file:///absolute/path"},
        ),
        (
            "name @ file://.",
            {"name": "name", "url": "file://."},
        ),
        (
            "name [fred,bar] @ http://foo.com ; python_version=='2.7'",
            {
                "name": "name",
                "url": "http://foo.com",
                "extras": ["fred", "bar"],
                "marker": 'python_version == "2.7"',
            },
        ),
        (
            "foo @ https://example.com/name;v=1.1/?query=foo&bar=baz#blah ;"
            " python_version=='3.4'",
            {
                "name": "foo",
                "url": "https://example.com/name;v=1.1/?query=foo&bar=baz#blah",
                "marker": 'python_version == "3.4"',
            },
        ),
        (
            'foo (>=1.2.3) ; python_version >= "2.7" and python_version < "2.8" or'
            ' python_version >= "3.4" and python_version < "3.5"',
            {
                "name": "foo",
                "constraint": ">=1.2.3",
                "marker": (
                    'python_version >= "2.7" and python_version < "2.8" or'
                    ' python_version >= "3.4" and python_version < "3.5"'
                ),
            },
        ),
    ],
)
def test_requirement(string: str, expected: dict[str, Any]) -> None:
    req = Requirement(string)

    assert_requirement(req, **expected)


@pytest.mark.parametrize(
    ["string", "exception"],
    [
        ("foo!", "Unexpected character at column 4\n\nfoo!\n   ^\n"),
        ("foo (>=bar)", 'invalid version constraint ">=bar"'),
        ("name @ file:.", "invalid URL"),
        ("name @ file:/.", "invalid URL"),
    ],
)
def test_invalid_requirement(string: str, exception: str) -> None:
    with pytest.raises(
        InvalidRequirement,
        match=re.escape(f"The requirement is invalid: {exception}"),
    ):
        Requirement(string)
