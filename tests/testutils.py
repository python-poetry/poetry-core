from __future__ import annotations

import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

import tomli_w

from poetry.core.utils._compat import tomllib


if TYPE_CHECKING:
    from collections.abc import Generator


__toml_build_backend_patch__ = {
    "build-system": {
        "requires": [str(Path(__file__).parent.parent)],
        "build-backend": "poetry.core.masonry.api",
    }
}


@contextmanager
def temporary_project_directory(
    path: Path, toml_patch: dict[str, Any] | None = None
) -> Generator[str, None, None]:
    """
    Context manager that takes a project source directory, copies content to a temporary
    directory, patches the `pyproject.toml` using the provided patch, or using the
    default patch if one is not given. The default path replaces `build-system` section
    in order to use the working copy of poetry-core as the backend.

    Once the context, exists, the temporary directory is cleaned up.

    :param path: Source project root directory to copy from.
    :param toml_patch: Patch to use for the pyproject.toml,
                        defaults to build system patching.
    :return: A temporary copy
    """
    assert (path / "pyproject.toml").exists()

    with tempfile.TemporaryDirectory(prefix="poetry-core-pep517") as tmp:
        dst = Path(tmp) / path.name
        shutil.copytree(str(path), dst)
        toml = dst / "pyproject.toml"
        with toml.open("rb") as f:
            data = tomllib.load(f)
        data.update(toml_patch or __toml_build_backend_patch__)
        with toml.open("wb") as f:
            tomli_w.dump(data, f)
        yield str(dst)


def subprocess_run(*args: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    """
    Helper method to run a subprocess. Asserts for success.
    """
    encoding = "locale" if sys.version_info >= (3, 10) else None
    result = subprocess.run(
        args, text=True, encoding=encoding, capture_output=True, **kwargs
    )
    assert result.returncode == 0
    return result


def validate_wheel_contents(
    name: str, version: str, path: Path, files: list[str] | None = None
) -> None:
    dist_info = f"{name}-{version}.dist-info"
    files = files or []

    with zipfile.ZipFile(path) as z:
        namelist = z.namelist()
        for filename in ["WHEEL", "METADATA", "RECORD", *files]:
            assert f"{dist_info}/{filename}" in namelist


def validate_sdist_contents(
    name: str, version: str, path: Path, files: list[str]
) -> None:
    escaped_name = name.replace("-", "_")
    with tarfile.open(path) as tar:
        namelist = tar.getnames()
        for filename in files:
            assert f"{escaped_name}-{version}/{filename}" in namelist
