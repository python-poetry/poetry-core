from .builders.complete import CompleteBuilder
from .builders.sdist import SdistBuilder
from .builders.wheel import WheelBuilder


class Builder:

    _FORMATS = {"sdist": SdistBuilder, "wheel": WheelBuilder, "all": CompleteBuilder}

    def __init__(self, poetry):
        self._poetry = poetry

    def build(self, fmt):
        if fmt not in self._FORMATS:
            raise ValueError("Invalid format: {}".format(fmt))

        builder = self._FORMATS[fmt](self._poetry)

        return builder.build()
