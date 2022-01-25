import sys

from typing import List


WINDOWS = sys.platform == "win32"


def list_to_shell_command(cmd: List[str]) -> str:
    executable = cmd[0]

    if " " in executable:
        executable = f'"{executable}"'
        cmd[0] = executable

    return " ".join(cmd)
