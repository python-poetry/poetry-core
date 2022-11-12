from __future__ import annotations

import hashlib
import io
import logging
import warnings

from typing import TYPE_CHECKING
from typing import Iterable

from poetry.core.packages.path_dependency import PathDependency


if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class FileDependency(PathDependency):
    def __init__(
        self,
        name: str,
        path: Path,
        groups: Iterable[str] | None = None,
        optional: bool = False,
        base: Path | None = None,
        extras: Iterable[str] | None = None,
    ) -> None:
        super().__init__(
            name,
            path,
            source_type="file",
            groups=groups,
            optional=optional,
            base=base,
            extras=extras,
        )

    def validate(self, *, raise_error: bool) -> bool:
        if not super().validate(raise_error=raise_error):
            return False

        if self._full_path.is_dir():
            message = (
                f"{self._full_path} for {self.pretty_name} is a directory,"
                " expected a file"
            )
            if raise_error:
                raise ValueError(message)
            logger.warning(message)
            return False
        return True

    def hash(self, hash_name: str = "sha256") -> str:
        warnings.warn(
            "hash() is deprecated. Use poetry.utils.helpers.get_file_hash() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        h = hashlib.new(hash_name)
        with self._full_path.open("rb") as fp:
            for content in iter(lambda: fp.read(io.DEFAULT_BUFFER_SIZE), b""):
                h.update(content)

        return h.hexdigest()
