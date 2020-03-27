import sys


try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

try:  # Python 2
    long = long
    unicode = unicode
    basestring = basestring
except NameError:  # Python 3
    long = int
    unicode = str
    basestring = str


PY2 = sys.version_info[0] == 2
PY34 = sys.version_info >= (3, 4)
PY35 = sys.version_info >= (3, 5)
PY36 = sys.version_info >= (3, 6)

WINDOWS = sys.platform == "win32"

if PY2:
    import pipes

    shell_quote = pipes.quote
else:
    import shlex

    shell_quote = shlex.quote

if PY2:
    from poetry.core._vendor.functools32 import lru_cache
else:
    from functools import lru_cache

if not PY35:
    from poetry.core._vendor.glob2 import glob
else:
    from glob import glob

if PY35:
    from pathlib import Path
else:
    from poetry.core._vendor.pathlib2 import Path

if not PY36:
    from collections import OrderedDict
else:
    OrderedDict = dict


def decode(string, encodings=None):
    if not PY2 and not isinstance(string, bytes):
        return string

    if PY2 and isinstance(string, unicode):
        return string

    encodings = encodings or ["utf-8", "latin1", "ascii"]

    for encoding in encodings:
        try:
            return string.decode(encoding)
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    return string.decode(encodings[0], errors="ignore")


def encode(string, encodings=None):
    if not PY2 and isinstance(string, bytes):
        return string

    if PY2 and isinstance(string, str):
        return string

    encodings = encodings or ["utf-8", "latin1", "ascii"]

    for encoding in encodings:
        try:
            return string.encode(encoding)
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    return string.encode(encodings[0], errors="ignore")


def to_str(string):
    if isinstance(string, str) or not isinstance(string, (unicode, bytes)):
        return string

    if PY2:
        method = "encode"
    else:
        method = "decode"

    encodings = ["utf-8", "latin1", "ascii"]

    for encoding in encodings:
        try:
            return getattr(string, method)(encoding)
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    return getattr(string, method)(encodings[0], errors="ignore")


def list_to_shell_command(cmd):
    executable = cmd[0]

    if " " in executable:
        executable = '"{}"'.format(executable)
        cmd[0] = executable

    return " ".join(cmd)
