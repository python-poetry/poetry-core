from __future__ import annotations

import contextlib
import sys

from pathlib import Path


__version__ = "0.0.0+in-tree"

with contextlib.suppress(ImportError):
    if sys.version_info < (3, 8):
        # compatibility for python <3.8
        import importlib_metadata as metadata
    else:
        from importlib import metadata

    with contextlib.suppress(metadata.PackageNotFoundError):
        __version__ = metadata.version("poetry-core")  # type: ignore[no-untyped-call]


__vendor_site__ = (Path(__file__).parent / "_vendor").as_posix()

if __vendor_site__ not in sys.path:
    sys.path.insert(0, __vendor_site__)
