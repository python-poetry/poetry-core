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


@pytest.fixture
def excluded_symlinks(tmp_path: Path) -> Path:
    root = fixtures_dir / "excluded_symlinks"
    tmp_root = tmp_path / "excluded_symlinks"
    shutil.copytree(root, tmp_root)

    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "file.txt").touch()

    package = tmp_root / "excluded_symlinks"
    try:
        # excluded via the "exclude" setting
        (package / "tests" / "broken").symlink_to(tmp_path / "missing")
        (package / "tests" / "outside").symlink_to(outside, target_is_directory=True)
        # excluded via VCS (get_ignored_files has to be mocked)
        (package / "vcs_ignored").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symlinks are not supported.")

    return tmp_root
