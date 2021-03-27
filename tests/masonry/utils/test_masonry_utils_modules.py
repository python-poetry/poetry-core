from pathlib import Path

import pytest

from poetry.core.masonry.utils.module import Module
from poetry.core.masonry.utils.module import ModuleOrPackageNotFound


def test_masonry_util_module_pep_561_stub_only_package_auto_detect():
    try:
        Module(
            name="pep_561-stubs",
            directory=str(
                Path(__file__).parent.parent
                / "builders"
                / "fixtures"
                / "pep_561_stub_only_auto_detect"
            ),
        )
    except ModuleOrPackageNotFound:
        pytest.fail("Stub-only package was not auto-detected")
