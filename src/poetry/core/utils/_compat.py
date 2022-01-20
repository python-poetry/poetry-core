import sys

from typing import List


PY37 = sys.version_info >= (3, 7)

WINDOWS = sys.platform == "win32"


try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


def list_to_shell_command(cmd: List[str]) -> str:
    executable = cmd[0]

    if " " in executable:
        executable = f'"{executable}"'
        cmd[0] = executable

    return " ".join(cmd)
