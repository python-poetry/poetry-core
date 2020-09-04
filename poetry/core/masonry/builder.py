from .builders.sdist import SdistBuilder
from .builders.wheel import WheelBuilder


class Builder:
    _FORMATS = {
        "sdist": SdistBuilder,
        "wheel": WheelBuilder,
    }

    def __init__(self, poetry):
        self._poetry = poetry

    def build(self, fmt="all"):
        if fmt in self._FORMATS:
            builders = [self._FORMATS[fmt]]
        elif fmt == "all":
            builders = self._FORMATS.values()
        else:
            raise ValueError("Invalid format: {}".format(fmt))

        for builder in builders:
            builder(self._poetry).build()
