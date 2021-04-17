from pathlib import Path
from typing import TYPE_CHECKING
from typing import Optional
from typing import Union


if TYPE_CHECKING:
    from poetry.core.poetry import Poetry  # noqa


class Builder:
    def __init__(self, poetry: "Poetry") -> None:
        from .builders.sdist import SdistBuilder
        from .builders.wheel import WheelBuilder

        self._poetry = poetry

        self._formats = {
            "sdist": SdistBuilder,
            "wheel": WheelBuilder,
        }

    def build(self, fmt: str, executable: Optional[Union[str, Path]] = None) -> None:
        if fmt in self._formats:
            builders = [self._formats[fmt]]
        elif fmt == "all":
            builders = self._formats.values()
        else:
            raise ValueError("Invalid format: {}".format(fmt))

        for builder in builders:
            builder(self._poetry, executable=executable).build()
