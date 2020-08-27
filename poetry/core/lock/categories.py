from enum import Enum


class LockCategory(Enum):
    MAIN = "main"
    DEV = "dev"

    def __eq__(self, other):
        if not isinstance(other, Enum):
            return self.value == other
        super(LockCategory, self).__eq__(other)
