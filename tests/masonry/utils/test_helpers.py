from __future__ import annotations

import pytest

from poetry.core.masonry.utils.helpers import escape_name
from poetry.core.masonry.utils.helpers import escape_version


@pytest.mark.parametrize(
    "version,expected",
    [
        ("1.2.3", "1.2.3"),
        ("1.2.3_1", "1.2.3_1"),
        ("1.2.3-1", "1.2.3_1"),
        ("1.2.3-1", "1.2.3_1"),
        ("2022.2", "2022.2"),
        ("12.20.12-----451---14-1-4-41", "12.20.12_451_14_1_4_41"),
        ("1.0b2.dev1", "1.0b2.dev1"),
        ("1.0+abc.7", "1.0+abc.7"),
    ],
)
def test_escape_version(version: str, expected: str) -> None:
    assert escape_version(version) == expected


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
    assert escape_name(name) == expected
