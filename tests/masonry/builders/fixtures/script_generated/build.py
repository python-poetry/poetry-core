from pathlib import Path
from setuptools.command.build_py import build_py


class BuildPyCommand(build_py):
    def run(self):
        with open('script_generated/generated/file.py', 'w') as out:
            print("#!/bin/env python3\nprint('Success!')\n", file=out)
        return super().run()


def build(setup_kwargs):
    setup_kwargs.update(
        {
            "cmdclass": {
                "build_py": BuildPyCommand,
            },
            "scripts": ["script_generated/generated/file.py"]
        }

    )
