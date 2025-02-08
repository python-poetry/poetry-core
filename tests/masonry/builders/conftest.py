from __future__ import annotations

import shutil

from pathlib import Path

import pytest


fixtures_dir = Path(__file__).parent / "fixtures"


@pytest.fixture
def complete_with_pycache_and_pyc_files(tmp_path: Path) -> Path:
    root = fixtures_dir / "complete"
    tmp_root = tmp_path / "complete"  # not git repo!

    shutil.copytree(root, tmp_root)
    for location in (".", "sub_pkg1"):
        abs_location = tmp_root / "my_package" / location
        (abs_location / "module1.cpython-39.pyc").touch()
        pycache_location = tmp_root / "my_package" / location / "__pycache__"
        pycache_location.mkdir(parents=True)
        (pycache_location / "module1.cpython-39.pyc").touch()
        (pycache_location / "some_other_file").touch()

    return tmp_root
