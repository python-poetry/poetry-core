from __future__ import annotations

import pytest

from poetry.core.packages.url_dependency import URLDependency
from poetry.core.version.markers import SingleMarker


def test_to_pep_508() -> None:
    dependency = URLDependency(
        "pytorch",
        "https://download.pytorch.org/whl/cpu/torch-1.5.1%2Bcpu-cp38-cp38-linux_x86_64.whl",
    )

    expected = (
        "pytorch @"
        " https://download.pytorch.org/whl/cpu/torch-1.5.1%2Bcpu-cp38-cp38-linux_x86_64.whl"
    )
    assert dependency.to_pep_508() == expected


def test_to_pep_508_with_extras() -> None:
    dependency = URLDependency(
        "pytorch",
        "https://download.pytorch.org/whl/cpu/torch-1.5.1%2Bcpu-cp38-cp38-linux_x86_64.whl",
        extras=["foo", "bar"],
    )

    expected = (
        "pytorch[bar,foo] @"
        " https://download.pytorch.org/whl/cpu/torch-1.5.1%2Bcpu-cp38-cp38-linux_x86_64.whl"
    )
    assert expected == dependency.to_pep_508()


def test_to_pep_508_with_subdirectory() -> None:
    dependency = URLDependency(
        "demo",
        "https://github.com/foo/bar/archive/0.1.0.zip",
        directory="baz",
    )

    expected = "demo @ https://github.com/foo/bar/archive/0.1.0.zip#subdirectory=baz"
    assert expected == dependency.to_pep_508()


def test_to_pep_508_with_marker() -> None:
    dependency = URLDependency(
        "pytorch",
        "https://download.pytorch.org/whl/cpu/torch-1.5.1%2Bcpu-cp38-cp38-linux_x86_64.whl",
    )
    dependency.marker = SingleMarker("sys.platform", "linux")

    expected = (
        "pytorch @"
        " https://download.pytorch.org/whl/cpu/torch-1.5.1%2Bcpu-cp38-cp38-linux_x86_64.whl"
        ' ; sys_platform == "linux"'
    )
    assert dependency.to_pep_508() == expected


@pytest.mark.parametrize(
    "name,url,extras,constraint,expected",
    [
        (
            "example",
            "https://example.org/example.whl",
            None,
            None,
            "example (*) @ https://example.org/example.whl",
        ),
        (
            "example",
            "https://example.org/example.whl",
            ["foo"],
            "1.2",
            "example[foo] (1.2) @ https://example.org/example.whl",
        ),
    ],
)
def test_directory_dependency_string_representation(
    name: str,
    url: str,
    extras: list[str] | None,
    constraint: str | None,
    expected: str,
) -> None:
    dependency = URLDependency(name=name, url=url, extras=extras)
    if constraint:
        dependency.constraint = constraint  # type: ignore[assignment]
    assert str(dependency) == expected
