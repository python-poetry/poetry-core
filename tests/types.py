from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Protocol


if TYPE_CHECKING:
    from pathlib import Path


class FixtureFactory(Protocol):
    def __call__(self, name: str, scope: Path | None = None) -> Path: ...
