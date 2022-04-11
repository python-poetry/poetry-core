from __future__ import annotations

import pytest

from poetry.core.packages.specification import PackageSpecification


@pytest.mark.parametrize(
    "spec1, spec2, expected_exact, expected_ignore_features",
    [
        (PackageSpecification("a"), PackageSpecification("a"), True, True),
        (PackageSpecification("a"), PackageSpecification("ab"), False, False),
        (
            PackageSpecification("a"),
            PackageSpecification("a", features=["c"]),
            False,
            True,
        ),
        (
            PackageSpecification("a", features=["c"]),
            PackageSpecification("a", features=["c", "d"]),
            False,
            True,
        ),
    ],
)
def test_is_same_package_ignore_features(
    spec1: PackageSpecification,
    spec2: PackageSpecification,
    expected_exact: bool,
    expected_ignore_features: bool,
) -> None:
    assert spec1.is_same_package_as(spec2) == expected_exact
    assert (
        spec1.is_same_package_as(spec2, ignore_features=True)
        == expected_ignore_features
    )
