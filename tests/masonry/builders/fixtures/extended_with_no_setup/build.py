import os
import shutil

from setuptools.command.build_ext import build_ext
from setuptools import Distribution, Extension


extensions = [Extension("extended.extended", ["extended/extended.c"])]


def build() -> None:
    distribution = Distribution({"name": "extended", "ext_modules": extensions})

    cmd = build_ext(distribution)
    cmd.finalize_options()
    cmd.run()

    # Copy built extensions back to the project
    for output in cmd.get_outputs():
        relative_extension = os.path.relpath(output, cmd.build_lib)
        shutil.copyfile(output, relative_extension)
        mode = os.stat(relative_extension).st_mode
        mode |= (mode & 0o444) >> 2
        os.chmod(relative_extension, mode)


if __name__ == "__main__":
    build()
