from __future__ import annotations

import pytest

from poetry.core.packages.specification import PackageSpecification


@pytest.mark.parametrize(
    "spec1, spec2, expected",
    [
        (PackageSpecification("a"), PackageSpecification("a"), True),
        (PackageSpecification("a", "type1"), PackageSpecification("a", "type1"), True),
        (PackageSpecification("a", "type1"), PackageSpecification("a", "type2"), False),
        (PackageSpecification("a"), PackageSpecification("a", "type1"), False),
        (PackageSpecification("a", "type1"), PackageSpecification("a"), False),
    ],
)
def test_is_same_package_source_type(
    spec1: PackageSpecification,
    spec2: PackageSpecification,
    expected: bool,
) -> None:
    assert spec1.is_same_package_as(spec2) == expected
