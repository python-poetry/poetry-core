from __future__ import annotations

import warnings


warnings.warn(
    "poetry.core.packages.constraints is deprecated."
    " Use poetry.core.constraints.generic instead.",
    DeprecationWarning,
    stacklevel=2,
)

from poetry.core.constraints.generic import *  # noqa: E402, F401, F403
