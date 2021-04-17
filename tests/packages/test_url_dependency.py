from poetry.core.packages.url_dependency import URLDependency
from poetry.core.version.markers import SingleMarker


def test_to_pep_508():
    dependency = URLDependency(
        "pytorch",
        "https://download.pytorch.org/whl/cpu/torch-1.5.1%2Bcpu-cp38-cp38-linux_x86_64.whl",
    )

    expected = "pytorch @ https://download.pytorch.org/whl/cpu/torch-1.5.1%2Bcpu-cp38-cp38-linux_x86_64.whl"
    assert expected == dependency.to_pep_508()


def test_to_pep_508_with_marker():
    dependency = URLDependency(
        "pytorch",
        "https://download.pytorch.org/whl/cpu/torch-1.5.1%2Bcpu-cp38-cp38-linux_x86_64.whl",
    )
    dependency.marker = SingleMarker("sys.platform", "linux")

    expected = 'pytorch @ https://download.pytorch.org/whl/cpu/torch-1.5.1%2Bcpu-cp38-cp38-linux_x86_64.whl ; sys_platform == "linux"'
    assert expected == dependency.to_pep_508()
