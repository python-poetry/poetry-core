from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from poetry.core.version.exceptions import InvalidVersionError
from poetry.core.version.pep440 import PEP440Version
from poetry.core.version.pep440 import Release
from poetry.core.version.pep440 import ReleaseTag


if TYPE_CHECKING:
    from collections.abc import Sequence


@pytest.mark.parametrize(
    "text,result",
    [
        ("1", PEP440Version(release=Release.from_parts(1))),
        ("1.2.3", PEP440Version(release=Release.from_parts(1, 2, 3))),
        (
            "1.2.3-1",
            PEP440Version(
                release=Release.from_parts(1, 2, 3), post=ReleaseTag("post", 1)
            ),
        ),
        (
            "1.2.3.dev1",
            PEP440Version(
                release=Release.from_parts(1, 2, 3), dev=ReleaseTag("dev", 1)
            ),
        ),
        (
            "1.2.3-1.dev1",
            PEP440Version(
                release=Release.from_parts(1, 2, 3),
                post=ReleaseTag("post", 1),
                dev=ReleaseTag("dev", 1),
            ),
        ),
        (
            "1.2.3+local",
            PEP440Version(release=Release.from_parts(1, 2, 3), local="local"),
        ),
        (
            "1.2.3+local.1",
            PEP440Version(release=Release.from_parts(1, 2, 3), local=("local", 1)),
        ),
        (
            "1.2.3+local1",
            PEP440Version(release=Release.from_parts(1, 2, 3), local="local1"),
        ),
        ("1.2.3+1", PEP440Version(release=Release.from_parts(1, 2, 3), local=1)),
        (
            "1.2.3a1",
            PEP440Version(
                release=Release.from_parts(1, 2, 3), pre=ReleaseTag("alpha", 1)
            ),
        ),
        (
            "1.2.3.a1",
            PEP440Version(
                release=Release.from_parts(1, 2, 3), pre=ReleaseTag("alpha", 1)
            ),
        ),
        (
            "1.2.3alpha1",
            PEP440Version(
                release=Release.from_parts(1, 2, 3), pre=ReleaseTag("alpha", 1)
            ),
        ),
        (
            "1.2.3b1",
            PEP440Version(
                release=Release.from_parts(1, 2, 3), pre=ReleaseTag("beta", 1)
            ),
        ),
        (
            "1.2.3.b1",
            PEP440Version(
                release=Release.from_parts(1, 2, 3), pre=ReleaseTag("beta", 1)
            ),
        ),
        (
            "1.2.3beta1",
            PEP440Version(
                release=Release.from_parts(1, 2, 3), pre=ReleaseTag("beta", 1)
            ),
        ),
        (
            "1.2.3rc1",
            PEP440Version(release=Release.from_parts(1, 2, 3), pre=ReleaseTag("rc", 1)),
        ),
        (
            "1.2.3.rc1",
            PEP440Version(release=Release.from_parts(1, 2, 3), pre=ReleaseTag("rc", 1)),
        ),
        (
            "2.2.0dev0+build.05669607",
            PEP440Version(
                release=Release.from_parts(2, 2, 0),
                dev=ReleaseTag("dev", 0),
                local=("build", "05669607"),
            ),
        ),
    ],
)
def test_pep440_parse_text(text: str, result: PEP440Version) -> None:
    assert PEP440Version.parse(text) == result


@pytest.mark.parametrize(
    "text", ["1.2.3.dev1-1", "example-1", "1.2.3-random1", "1.2.3-1-1"]
)
def test_pep440_parse_text_invalid_versions(text: str) -> None:
    with pytest.raises(InvalidVersionError):
        PEP440Version.parse(text)


@pytest.mark.parametrize(
    ("version", "major", "minor", "patch", "non_semver_parts", "parts"),
    [
        ("1", 1, None, None, (), (1,)),
        ("1.2", 1, 2, None, (), (1, 2)),
        ("1.2.3", 1, 2, 3, (), (1, 2, 3)),
        ("1.2.3.4", 1, 2, 3, (4,), (1, 2, 3, 4)),
        ("1.2.3.4.5", 1, 2, 3, (4, 5), (1, 2, 3, 4, 5)),
        ("9!1.2.3.4.5a6.post7.dev8", 1, 2, 3, (4, 5), (1, 2, 3, 4, 5)),
    ],
)
def test_properties(
    version: str,
    major: int,
    minor: int | None,
    patch: int | None,
    non_semver_parts: Sequence[int],
    parts: Sequence[int],
) -> None:
    v = PEP440Version.parse(version)
    assert v.major == major
    assert v.minor == minor
    assert v.patch == patch
    assert v.non_semver_parts == non_semver_parts
    assert v.parts == parts


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", False),
        ("1.dev0", False),
        ("1.a0", True),
        ("1.b1", True),
        ("1.rc3", True),
        ("1.a0.dev0", True),
        ("9!1.2.3a1.post2.dev3", True),
    ],
)
def test_is_prerelease(version: str, expected: bool) -> None:
    v = PEP440Version.parse(version)
    assert v.is_prerelease() is expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", False),
        ("1.post1", True),
        ("9!1.2.3a1.post2.dev3", True),
    ],
)
def test_is_postrelease(version: str, expected: bool) -> None:
    v = PEP440Version.parse(version)
    assert v.is_postrelease() is expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", False),
        ("1.dev0", True),
        ("1.a0.dev0", True),
        ("9!1.2.3a1.post2.dev3", True),
    ],
)
def test_is_devrelease(version: str, expected: bool) -> None:
    v = PEP440Version.parse(version)
    assert v.is_devrelease() is expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", False),
        ("1+local", True),
        ("1+local.dev0", True),
        ("9!1.2.3a1.post2.dev3+local", True),
    ],
)
def test_is_local(version: str, expected: bool) -> None:
    v = PEP440Version.parse(version)
    assert v.is_local() is expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", True),
        ("1.2", True),
        ("1+local", True),
        ("1.dev0", False),
        ("1a0", False),
        ("1.post0", False),
    ],
)
def test_is_no_suffix_release(version: str, expected: bool) -> None:
    v = PEP440Version.parse(version)
    assert v.is_no_suffix_release() is expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", True),
        ("1.2", True),
        ("1.2.3", True),
        ("2!1.2.3", True),
        ("1.2.3+local", True),
        ("1.2.3.4", True),
        ("1.dev0", False),
        ("1.2dev0", False),
        ("1.2.3dev0", False),
        ("1.2.3.4dev0", False),
        ("1.post1", True),
        ("1.2.post1", True),
        ("1.2.3.post1", True),
        ("1.post1.dev0", False),
        ("1.2.post1.dev0", False),
        ("1.2.3.post1.dev0", False),
        ("1.a1", False),
        ("1.2a1", False),
        ("1.2.3a1", False),
        ("1.2.3.4a1", False),
        ("1.a1.post2", False),
        ("1.2a1.post2", False),
        ("1.2.3a1.post2", False),
        ("1.2.3.4a1.post2", False),
        ("1.a1.post2.dev0", False),
        ("1.2a1.post2.dev0", False),
        ("1.2.3a1.post2.dev0", False),
        ("1.2.3.4a1.post2.dev0", False),
    ],
)
def test_is_stable(version: str, expected: bool) -> None:
    subject = PEP440Version.parse(version)

    assert subject.is_stable() is expected
    assert subject.is_unstable() is not expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("0", True),
        ("0.2", True),
        ("0.2.3", True),
        ("2!0.2.3", True),
        ("0.2.3+local", True),
        ("0.2.3.4", True),
        ("0.dev0", False),
        ("0.2dev0", False),
        ("0.2.3dev0", False),
        ("0.2.3.4dev0", False),
        ("0.post1", True),
        ("0.2.post1", True),
        ("0.2.3.post1", True),
        ("0.post1.dev0", False),
        ("0.2.post1.dev0", False),
        ("0.2.3.post1.dev0", False),
        ("0.a1", False),
        ("0.2a1", False),
        ("0.2.3a1", False),
        ("0.2.3.4a1", False),
        ("0.a1.post2", False),
        ("0.2a1.post2", False),
        ("0.2.3a1.post2", False),
        ("0.2.3.4a1.post2", False),
        ("0.a1.post2.dev0", False),
        ("0.2a1.post2.dev0", False),
        ("0.2.3a1.post2.dev0", False),
        ("0.2.3.4a1.post2.dev0", False),
    ],
)
def test_is_stable_all_major_0_versions_are_treated_as_normal_versions(
    version: str, expected: bool
) -> None:
    subject = PEP440Version.parse(version)

    assert subject.is_stable() is expected
    assert subject.is_unstable() is not expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", "2"),
        ("2!1", "2!2"),
        ("1+local", "2"),
        ("1.2", "2.0"),
        ("1.2.3", "2.0.0"),
        ("1.2.3.4", "2.0.0.0"),
        ("1.dev0", "1"),
        ("1.2.dev0", "2.0"),
        ("1.post1", "2"),
        ("1.2.post1", "2.0"),
        ("1.post1.dev0", "2"),
        ("1.2.post1.dev0", "2.0"),
        ("1.a1", "1"),
        ("1.2a1", "2.0"),
        ("1.a1.post2", "1"),
        ("1.2a1.post2", "2.0"),
        ("1.a1.post2.dev0", "1"),
        ("1.2a1.post2.dev0", "2.0"),
    ],
)
def test_next_major(version: str, expected: str) -> None:
    v = PEP440Version.parse(version)
    assert v.next_major().text == expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", "1.1"),
        ("1.2", "1.3"),
        ("2!1.2", "2!1.3"),
        ("1.2+local", "1.3"),
        ("1.2.3", "1.3.0"),
        ("1.2.3.4", "1.3.0.0"),
        ("1.dev0", "1"),
        ("1.2dev0", "1.2"),
        ("1.2.3dev0", "1.3.0"),
        ("1.post1", "1.1"),
        ("1.2.post1", "1.3"),
        ("1.2.3.post1", "1.3.0"),
        ("1.post1.dev0", "1.1"),
        ("1.2.post1.dev0", "1.3"),
        ("1.a1", "1"),
        ("1.2a1", "1.2"),
        ("1.2.3a1", "1.3.0"),
        ("1.a1.post2", "1"),
        ("1.2a1.post2", "1.2"),
        ("1.2.3a1.post2", "1.3.0"),
        ("1.a1.post2.dev0", "1"),
        ("1.2a1.post2.dev0", "1.2"),
        ("1.2.3a1.post2.dev0", "1.3.0"),
    ],
)
def test_next_minor(version: str, expected: str) -> None:
    v = PEP440Version.parse(version)
    assert v.next_minor().text == expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", "1.0.1"),
        ("1.2", "1.2.1"),
        ("1.2.3", "1.2.4"),
        ("2!1.2.3", "2!1.2.4"),
        ("1.2.3+local", "1.2.4"),
        ("1.2.3.4", "1.2.4.0"),
        ("1.dev0", "1"),
        ("1.2dev0", "1.2"),
        ("1.2.3dev0", "1.2.3"),
        ("1.2.3.4dev0", "1.2.4.0"),
        ("1.post1", "1.0.1"),
        ("1.2.post1", "1.2.1"),
        ("1.2.3.post1", "1.2.4"),
        ("1.post1.dev0", "1.0.1"),
        ("1.2.post1.dev0", "1.2.1"),
        ("1.2.3.post1.dev0", "1.2.4"),
        ("1.a1", "1"),
        ("1.2a1", "1.2"),
        ("1.2.3a1", "1.2.3"),
        ("1.2.3.4a1", "1.2.4.0"),
        ("1.a1.post2", "1"),
        ("1.2a1.post2", "1.2"),
        ("1.2.3a1.post2", "1.2.3"),
        ("1.2.3.4a1.post2", "1.2.4.0"),
        ("1.a1.post2.dev0", "1"),
        ("1.2a1.post2.dev0", "1.2"),
        ("1.2.3a1.post2.dev0", "1.2.3"),
        ("1.2.3.4a1.post2.dev0", "1.2.4.0"),
    ],
)
def test_next_patch(version: str, expected: str) -> None:
    v = PEP440Version.parse(version)
    assert v.next_patch().text == expected


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        # simple versions (only "release" attribute) are tested in test_segments
        # via Release.next()
        ("1", "2"),
        ("2!1", "2!2"),
        ("1+local", "2+local"),
        ("1.post4", "2"),
        ("1.dev4", "1"),
        ("1.a4", "1"),
    ],
)
def test_next_stable(version: str, expected: str) -> None:
    v = PEP440Version.parse(version)
    assert v.next_stable().text == expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1.2a1", "1.2a2"),
        ("2!1.2a1", "2!1.2a2"),
        ("1.2dev0", "1.2a0"),
        ("1.2a1.dev0", "1.2a1"),
        ("1.2a1.post1.dev0", "1.2a2"),
    ],
)
def test_next_prerelease(version: str, expected: str) -> None:
    v = PEP440Version.parse(version)
    assert v.next_prerelease().text == expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", "1.post0"),
        ("1.post1", "1.post2"),
        ("9!1.2.3.4", "9!1.2.3.4.post0"),
        ("9!1.2.3.4.post2", "9!1.2.3.4.post3"),
        ("1.dev0", "1.post0"),
        ("1.post1.dev0", "1.post1"),
        ("1a1", "1a1.post0"),
        ("1a1.dev0", "1a1.post0"),
        ("1a1.post2", "1a1.post3"),
        ("1a1.post2.dev0", "1a1.post2"),
    ],
)
def test_next_postrelease(version: str, expected: str) -> None:
    v = PEP440Version.parse(version)
    assert v.next_postrelease().text == expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("0.dev0", "0.dev1"),
        ("9!1.2.3a1.post2.dev3", "9!1.2.3a1.post2.dev4"),
    ],
)
def test_next_devrelease(version: str, expected: str) -> None:
    v = PEP440Version.parse(version)
    assert v.next_devrelease().text == expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", "1a0"),
        ("9!1.2.3a1.post2.dev3", "9!1.2.3a0"),
    ],
)
def test_first_prerelease(version: str, expected: str) -> None:
    v = PEP440Version.parse(version)
    assert v.first_prerelease().text == expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", "1.dev0"),
        ("1a1", "1a1.dev0"),
        ("1.post2", "1.post2.dev0"),
        ("9!1.2.3a1.post2.dev3", "9!1.2.3a1.post2.dev0"),
    ],
)
def test_first_devrelease(version: str, expected: str) -> None:
    v = PEP440Version.parse(version)
    assert v.first_devrelease().text == expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", "1"),
        ("1+local.dev0", "1"),
        ("9!1.2.3a1.post2.dev3+local", "9!1.2.3a1.post2.dev3"),
    ],
)
def test_without_local(version: str, expected: str) -> None:
    v = PEP440Version.parse(version)
    assert v.without_local().text == expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", "1"),
        ("1.dev0", "1.dev0"),
        ("9!1.2.3a1.post2.dev3", "9!1.2.3a1"),
    ],
)
def test_without_postrelease(version: str, expected: str) -> None:
    v = PEP440Version.parse(version)
    assert v.without_postrelease().text == expected


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1", "1"),
        ("1.dev0", "1"),
        ("9!1.2.3a1.post2.dev3", "9!1.2.3a1.post2"),
    ],
)
def test_without_devrelease(version: str, expected: str) -> None:
    v = PEP440Version.parse(version)
    assert v.without_devrelease().text == expected
