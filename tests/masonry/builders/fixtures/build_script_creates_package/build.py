import os
import shutil


package = "my_package"
source = "src_my_package"


def build() -> None:
    if os.path.isdir(package):
        shutil.rmtree(package)
    shutil.copytree("src_my_package", package)


if __name__ == "__main__":
    build()
