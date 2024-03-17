from pathlib import Path
from setuptools.command.build_py import build_py


class BuildPyCommand(build_py):
    def run(self):
        with open("generated_script_file/generated/script.sh", "w", encoding="utf-8") as f:
            f.write('#!/usr/bin/env bash\n\necho "Hello World!"\n')
        ret = super().run()
        return ret


def build(setup_kwargs):
    setup_kwargs["cmdclass"] = {"build_py": BuildPyCommand}
