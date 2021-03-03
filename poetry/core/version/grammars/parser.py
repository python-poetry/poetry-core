import os

from typing import TYPE_CHECKING
from typing import Optional


if TYPE_CHECKING:
    from lark import Lark  # noqa
    from lark import Tree  # noqa


class Parser:
    def __init__(self, grammar: str) -> None:
        self._grammar = grammar
        self._parser: Optional["Lark"] = None

    def parse(self, string: str) -> "Tree":
        from lark import Lark

        if self._parser is None:
            self._parser = Lark.open(
                os.path.join(os.path.dirname(__file__), f"{self._grammar}.lark"),
                parser="lalr",
            )

        return self._parser.parse(string)
