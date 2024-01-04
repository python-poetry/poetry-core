from __future__ import annotations

from typing import TYPE_CHECKING

from poetry.core.masonry.builders.sdist import SdistBuilder
from poetry.core.masonry.builders.wheel import WheelBuilder


if TYPE_CHECKING:
    from pathlib import Path

    from poetry.core.poetry import Poetry


BUILD_FORMATS = {
    "sdist": SdistBuilder,
    "wheel": WheelBuilder,
}


class Builder:
    def __init__(self, poetry: Poetry) -> None:
        self._poetry = poetry

    def build(
        self,
        fmt: str,
        executable: str | Path | None = None,
        *,
        target_dir: Path | None = None,
    ) -> None:
        if fmt in BUILD_FORMATS:
            builders = [BUILD_FORMATS[fmt]]
        elif fmt == "all":
            builders = list(BUILD_FORMATS.values())
        else:
            raise ValueError(f"Invalid format: {fmt}")

        for builder in builders:
            builder(self._poetry, executable=executable).build(target_dir)
