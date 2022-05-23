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


@pytest.mark.parametrize(
    ("source_type", "result"),
    [
        ("directory", True),
        ("file", True),
        ("url", True),
        ("git", True),
        ("legacy", False),
        (None, False),
    ],
)
def test_is_direct_origin(source_type: str | None, result: bool) -> None:
    assert PackageSpecification("package", source_type).is_direct_origin() == result


@pytest.mark.parametrize(
    "spec1, spec2, expected",
    [
        (PackageSpecification("a"), PackageSpecification("a"), True),
        (PackageSpecification("a"), PackageSpecification("b"), False),
        (PackageSpecification("a", features=["x"]), PackageSpecification("a"), True),
        (
            PackageSpecification("a", features=["x"]),
            PackageSpecification("a", features=["x"]),
            True,
        ),
        (
            PackageSpecification("a", features=["x"]),
            PackageSpecification("b", features=["x"]),
            False,
        ),
        (
            PackageSpecification("a", features=["x"]),
            PackageSpecification("a", features=["y"]),
            False,
        ),
        (
            PackageSpecification("a", features=["x"]),
            PackageSpecification("a", features=["x", "y"]),
            False,
        ),
        (
            PackageSpecification("a", features=["x", "y"]),
            PackageSpecification("a", features=["x"]),
            True,
        ),
    ],
)
def test_specification_provides(
    spec1: PackageSpecification,
    spec2: PackageSpecification,
    expected: bool,
) -> None:
    assert spec1.provides(spec2) == expected
