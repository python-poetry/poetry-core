from __future__ import annotations

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
