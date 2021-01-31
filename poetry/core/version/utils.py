from typing import Any


class Infinity(object):
    def __repr__(self) -> str:
        return "Infinity"

    def __hash__(self) -> int:
        return hash(repr(self))

    def __lt__(self, other: Any) -> bool:
        return False

    def __le__(self, other: Any) -> bool:
        return False

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__)

    def __ne__(self, other: Any) -> bool:
        return not isinstance(other, self.__class__)

    def __gt__(self, other: Any) -> bool:
        return True

    def __ge__(self, other: Any) -> bool:
        return True

    def __neg__(self) -> "NegativeInfinity":
        return NegativeInfinity


Infinity = Infinity()  # type: ignore


class NegativeInfinity(object):
    def __repr__(self) -> str:
        return "-Infinity"

    def __hash__(self) -> int:
        return hash(repr(self))

    def __lt__(self, other: Any) -> bool:
        return True

    def __le__(self, other: Any) -> bool:
        return True

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__)

    def __ne__(self, other: Any) -> bool:
        return not isinstance(other, self.__class__)

    def __gt__(self, other: Any) -> bool:
        return False

    def __ge__(self, other: Any) -> bool:
        return False

    def __neg__(self) -> Infinity:
        return Infinity


NegativeInfinity = NegativeInfinity()  # type: ignore
