import shutil
import subprocess
import tarfile
import zipfile

from contextlib import contextmanager
from pathlib import Path
from typing import Any
from typing import ContextManager
from typing import Dict
from typing import List
from typing import Optional

from poetry.core.toml import TOMLFile
from poetry.core.utils._compat import PY37


try:
    from backports import tempfile
except ImportError:
    import tempfile


__toml_build_backend_patch__ = {
    "build-system": {
        "requires": [str(Path(__file__).parent.parent)],
        "build-backend": "poetry.core.masonry.api",
    }
}


@contextmanager
def temporary_project_directory(
    path, toml_patch=None
):  # type: (Path, Optional[Dict[str, Any]]) -> ContextManager[str]
    """
    Context manager that takes a project source directory, copies content to a temporary
    directory, patches the `pyproject.toml` using the provided patch, or using the default
    patch if one is not given. The default path replaces `build-system` section in order
    to use the working copy of poetry-core as the backend.

    Once the context, exists, the temporary directory is cleaned up.

    :param path: Source project root directory to copy from.
    :param toml_patch: Patch to use for the pyproject.toml, defaults to build system patching.
    :return: A temporary copy
    """
    assert (path / "pyproject.toml").exists()

    with tempfile.TemporaryDirectory(prefix="poetry-core-pep517") as tmp:
        dst = Path(tmp) / path.name
        shutil.copytree(str(path), dst)
        toml = TOMLFile(str(dst / "pyproject.toml"))
        data = toml.read()
        data.update(toml_patch or __toml_build_backend_patch__)
        toml.write(data)
        yield str(dst)


def subprocess_run(*args, **kwargs):  # type: (str, Any) -> subprocess.CompletedProcess
    """
    Helper method to run a subprocess. Asserts for success.
    """
    compat_kwargs = {"text" if PY37 else "universal_newlines": True}
    result = subprocess.run(
        args, **compat_kwargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs
    )
    assert result.returncode == 0
    return result


def validate_wheel_contents(
    name, version, path, files=None
):  # type: (str, str, str, Optional[List[str]]) -> None
    dist_info = "{}-{}.dist-info".format(name, version)
    files = files or []

    with zipfile.ZipFile(path) as z:
        namelist = z.namelist()
        # we use concatenation here for PY2 compat
        for filename in ["WHEEL", "METADATA", "RECORD"] + files:
            assert "{}/{}".format(dist_info, filename) in namelist


def validate_sdist_contents(
    name, version, path, files
):  # type: (str, str, str, List[str]) -> None
    with tarfile.open(path) as tar:
        namelist = tar.getnames()
        for filename in files:
            assert "{}-{}/{}".format(name, version, filename) in namelist
