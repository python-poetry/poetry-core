from typing import Optional
from typing import Union

from poetry.core.utils._compat import Path

from .builders.complete import CompleteBuilder
from .builders.sdist import SdistBuilder
from .builders.wheel import WheelBuilder


class Builder:

    _FORMATS = {"sdist": SdistBuilder, "wheel": WheelBuilder, "all": CompleteBuilder}

    def __init__(self, poetry):
        self._poetry = poetry

    def build(
        self, fmt, executable=None
    ):  # type: (str, Optional[Union[str, Path]]) -> None
        if fmt not in self._FORMATS:
            raise ValueError("Invalid format: {}".format(fmt))

        builder = self._FORMATS[fmt](self._poetry, executable=executable)

        return builder.build()
