from .builders.sdist import SdistBuilder
from .builders.wheel import WheelBuilder


class Builder:
    _FORMATS = {
        "sdist": [SdistBuilder],
        "wheel": [WheelBuilder],
        "all": [SdistBuilder, WheelBuilder],
    }

    def __init__(self, poetry):
        self._poetry = poetry

    def build(self, fmt):
        if fmt not in self._FORMATS:
            raise ValueError("Invalid format: {}".format(fmt))

        for builder in self._FORMATS[fmt]:
            builder(self._poetry).build()
