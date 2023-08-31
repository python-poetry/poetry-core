from pathlib import Path
from setuptools.command.build_py import build_py


class BuildPyCommand(build_py):
    def run(self):
        gen_file = Path("build_with_build_py_only/generated/file.py")
        gen_file.touch()
        ret = super().run()
        gen_file.unlink()
        return ret


def build(setup_kwargs):
    setup_kwargs["cmdclass"] = {"build_py": BuildPyCommand}
