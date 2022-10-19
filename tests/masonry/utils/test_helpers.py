from __future__ import annotations

import warnings

import pytest

from poetry.core.masonry.utils.helpers import escape_name


@pytest.mark.parametrize(
    "name,expected",
    [
        ("foo", "foo"),
        ("foo-bar", "foo_bar"),
        ("FOO-bAr", "foo_bar"),
        ("foo.bar", "foo_bar"),
        ("foo123-ba---.r", "foo123_ba_r"),
    ],
)
def test_escape_name(name: str, expected: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert escape_name(name) == expected
