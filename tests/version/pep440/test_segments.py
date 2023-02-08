from __future__ import annotations

import pytest

from poetry.core.version.pep440 import Release
from poetry.core.version.pep440 import ReleaseTag
from poetry.core.version.pep440.segments import RELEASE_PHASE_NORMALIZATIONS


def test_release_post_init_minor_and_patch() -> None:
    """
    Minor and patch must not be None but zero if there are extra parts.
    """
    release = Release(1, extra=(0,))
    assert release.minor == 0
    assert release.patch == 0


def test_release_post_init_zero_version() -> None:
    """
    Smoke test for edge case (because zeros are stripped for comparison).
    """
    Release(0)


@pytest.mark.parametrize("precision1", range(1, 6))
@pytest.mark.parametrize("precision2", range(1, 6))
def test_release_equal_zero_padding(precision1: int, precision2: int) -> None:
    release1 = Release.from_parts(*range(1, precision1 + 1))
    if precision1 > precision2:
        # e.g. 1.2.3 != 1.2
        release2 = Release.from_parts(*range(1, precision2 + 1))
        assert release1 != release2
        assert release2 != release1
    else:
        # e.g. 1.2 == 1.2.0
        release2 = Release.from_parts(
            *range(1, precision1 + 1), *[0] * (precision2 - precision1)
        )
        assert release1 == release2
        assert release2 == release1


@pytest.mark.parametrize(
    "parts,result",
    [
        ((1,), Release(1)),
        ((1, 2), Release(1, 2)),
        ((1, 2, 3), Release(1, 2, 3)),
        ((1, 2, 3, 4), Release(1, 2, 3, (4,))),
        ((1, 2, 3, 4, 5, 6), Release(1, 2, 3, (4, 5, 6))),
    ],
)
def test_release_from_parts(parts: tuple[int, ...], result: Release) -> None:
    assert Release.from_parts(*parts) == result


@pytest.mark.parametrize("precision", list(range(1, 6)))
def test_release_precision(precision: int) -> None:
    """
    Semantically identical releases might have a different precision, e.g. 1 vs. 1.0
    """
    assert Release.from_parts(1, *[0] * (precision - 1)).precision == precision


@pytest.mark.parametrize("precision", list(range(1, 6)))
def test_release_text(precision: int) -> None:
    increments = list(range(1, precision + 1))
    zeros = [1] + [0] * (precision - 1)

    assert Release.from_parts(*increments).text == ".".join(str(i) for i in increments)
    assert Release.from_parts(*zeros).text == ".".join(str(i) for i in zeros)


@pytest.mark.parametrize("precision", list(range(1, 6)))
def test_release_next_major(precision: int) -> None:
    release = Release.from_parts(1, *[0] * (precision - 1))
    expected = Release.from_parts(2, *[0] * (precision - 1))
    assert release.next_major() == expected


@pytest.mark.parametrize("precision", list(range(1, 6)))
def test_release_next_minor(precision: int) -> None:
    release = Release.from_parts(1, *[0] * (precision - 1))
    expected = Release.from_parts(1, 1, *[0] * (precision - 2))
    assert release.next_minor() == expected


@pytest.mark.parametrize("precision", list(range(1, 6)))
def test_release_next_patch(precision: int) -> None:
    release = Release.from_parts(1, *[0] * (precision - 1))
    expected = Release.from_parts(1, 0, 1, *[0] * (precision - 3))
    assert release.next_patch() == expected


@pytest.mark.parametrize(
    "parts,result",
    [
        (("a",), ReleaseTag("alpha", 0)),
        (("a", 1), ReleaseTag("alpha", 1)),
        (("b",), ReleaseTag("beta", 0)),
        (("b", 1), ReleaseTag("beta", 1)),
        (("pre",), ReleaseTag("preview", 0)),
        (("pre", 1), ReleaseTag("preview", 1)),
        (("c",), ReleaseTag("rc", 0)),
        (("c", 1), ReleaseTag("rc", 1)),
        (("r",), ReleaseTag("rev", 0)),
        (("r", 1), ReleaseTag("rev", 1)),
    ],
)
def test_release_tag_normalisation(
    parts: tuple[str] | tuple[str, int], result: ReleaseTag
) -> None:
    tag = ReleaseTag(*parts)
    assert tag == result
    assert tag.to_string() == result.to_string()


@pytest.mark.parametrize(
    "parts,result",
    [
        (("a",), ReleaseTag("beta")),
        (("b",), ReleaseTag("rc")),
        (("post",), None),
        (("rc",), None),
        (("rev",), None),
        (("dev",), None),
    ],
)
def test_release_tag_next_phase(parts: tuple[str], result: ReleaseTag | None) -> None:
    assert ReleaseTag(*parts).next_phase() == result


@pytest.mark.parametrize("phase", list({*RELEASE_PHASE_NORMALIZATIONS.keys()}))
def test_release_tag_next(phase: str) -> None:
    tag = ReleaseTag(phase=phase).next()
    assert tag.phase == RELEASE_PHASE_NORMALIZATIONS[phase]
    assert tag.number == 1
