from typing import List
from typing import Optional


# TODO: Convert to dataclass once python 2.7, 3.5 is dropped
class BuildSystem:
    def __init__(
        self, build_backend=None, requires=None
    ):  # type: (Optional[str], Optional[List[str]]) -> None
        self.build_backend = (
            build_backend
            if build_backend is not None
            else "setuptools.build_meta:__legacy__"
        )
        self.requires = requires if requires is not None else ["setuptools", "wheel"]
