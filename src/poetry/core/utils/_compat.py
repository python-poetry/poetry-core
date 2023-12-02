from __future__ import annotations

import sys


WINDOWS = sys.platform == "win32"


if sys.version_info < (3, 11):
    # compatibility for python <3.11
    import tomli as tomllib
else:
    import tomllib

if sys.version_info < (3, 9):
    import importlib_resources
else:
    from importlib import resources as importlib_resources

__all__ = ["tomllib", "importlib_resources"]
