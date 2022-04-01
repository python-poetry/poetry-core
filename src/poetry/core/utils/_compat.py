from __future__ import annotations

import sys


WINDOWS = sys.platform == "win32"


def list_to_shell_command(cmd: list[str]) -> str:
    executable = cmd[0]

    if " " in executable:
        executable = f'"{executable}"'
        cmd[0] = executable

    return " ".join(cmd)
