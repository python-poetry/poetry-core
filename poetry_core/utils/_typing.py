from ._compat import PY35


if not PY35:
    from poetry_core._vendor.typing import Any
    from poetry_core._vendor.typing import Callable
    from poetry_core._vendor.typing import Dict
    from poetry_core._vendor.typing import FrozenSet
    from poetry_core._vendor.typing import Generator
    from poetry_core._vendor.typing import IO
    from poetry_core._vendor.typing import Iterable
    from poetry_core._vendor.typing import Iterator
    from poetry_core._vendor.typing import List
    from poetry_core._vendor.typing import Optional
    from poetry_core._vendor.typing import Sequence
    from poetry_core._vendor.typing import Set
    from poetry_core._vendor.typing import SupportsInt
    from poetry_core._vendor.typing import Tuple
    from poetry_core._vendor.typing import Union
else:
    from typing import Any
    from typing import Callable
    from typing import Dict
    from typing import FrozenSet
    from typing import Generator
    from typing import IO
    from typing import Iterable
    from typing import Iterator
    from typing import List
    from typing import Optional
    from typing import Sequence
    from typing import Set
    from typing import SupportsInt
    from typing import Tuple
    from typing import Union
