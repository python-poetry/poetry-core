import dataclasses

from typing import Optional
from typing import Tuple
from typing import Union


RELEASE_PHASE_ALPHA = "alpha"
RELEASE_PHASE_BETA = "beta"
RELEASE_PHASE_RC = "rc"
RELEASE_PHASE_PREVIEW = "preview"
RELEASE_PHASE_POST = "post"
RELEASE_PHASE_REV = "rev"
RELEASE_PHASE_DEV = "dev"
RELEASE_PHASES = {
    RELEASE_PHASE_ALPHA: "a",
    RELEASE_PHASE_BETA: "b",
    RELEASE_PHASE_RC: "c",
    RELEASE_PHASE_PREVIEW: "pre",
    RELEASE_PHASE_POST: "-",  # shorthand of 1.2.3-post1 is 1.2.3-1
    RELEASE_PHASE_REV: "r",
    RELEASE_PHASE_DEV: "dev",
}
RELEASE_PHASES_SHORT = {v: k for k, v in RELEASE_PHASES.items() if k != "post"}


@dataclasses.dataclass(frozen=True, eq=True, order=True)
class Release:
    major: int = dataclasses.field(default=0, compare=False)
    minor: Optional[int] = dataclasses.field(default=None, compare=False)
    patch: Optional[int] = dataclasses.field(default=None, compare=False)
    # some projects use non-semver versioning schemes, eg: 1.2.3.4
    extra: Optional[Union[int, Tuple[int, ...]]] = dataclasses.field(
        default=None, compare=False
    )
    precision: int = dataclasses.field(default=None, init=False, compare=False)
    text: str = dataclasses.field(default=None, init=False, compare=False)
    _compare_key: Tuple[int, ...] = dataclasses.field(
        default=None, init=False, compare=True
    )

    def __post_init__(self):
        if self.extra is None:
            object.__setattr__(self, "extra", tuple())
        elif not isinstance(self.extra, tuple):
            object.__setattr__(self, "extra", (self.extra,))

        parts = list(
            map(
                str,
                filter(
                    lambda x: x is not None,
                    [self.major, self.minor, self.patch, *self.extra],
                ),
            )
        )
        object.__setattr__(self, "text", ".".join(parts))
        object.__setattr__(self, "precision", len(parts))
        object.__setattr__(
            self,
            "_compare_key",
            (self.major, self.minor or 0, self.patch or 0, *self.extra),
        )

    @classmethod
    def from_parts(cls, *parts: int) -> "Release":
        if not parts:
            return cls()

        return cls(
            major=parts[0],
            minor=parts[1] if len(parts) > 1 else None,
            patch=parts[2] if len(parts) > 2 else None,
            extra=parts[3:] if len(parts) > 3 else tuple(),
        )

    def to_string(self) -> str:
        return self.text

    def next_major(self) -> "Release":
        return dataclasses.replace(
            self,
            major=self.major + 1,
            minor=0 if self.minor is not None else None,
            patch=0 if self.patch is not None else None,
            extra=tuple(0 for _ in self.extra),
        )

    def next_minor(self) -> "Release":
        return dataclasses.replace(
            self,
            major=self.major,
            minor=self.minor + 1 if self.minor is not None else 1,
            patch=0 if self.patch is not None else None,
            extra=tuple(0 for _ in self.extra),
        )

    def next_patch(self) -> "Release":
        return dataclasses.replace(
            self,
            major=self.major,
            minor=self.minor if self.minor is not None else 0,
            patch=self.patch + 1 if self.patch is not None else 1,
            extra=tuple(0 for _ in self.extra),
        )


@dataclasses.dataclass(frozen=True, eq=True, order=True)
class ReleaseTag:
    phase: str
    number: int = dataclasses.field(default=0)

    def __post_init__(self):
        object.__setattr__(self, "phase", self.expand(self.phase))

    @classmethod
    def shorten(cls, phase: str) -> str:
        return RELEASE_PHASES.get(phase, phase)

    @classmethod
    def expand(cls, phase: str) -> str:
        return RELEASE_PHASES_SHORT.get(phase, phase)

    def to_string(self, short: bool = False) -> str:
        if short:
            return f"{self.shorten(self.phase)}{self.number}"
        return f"{self.phase}.{self.number}"

    def next(self) -> "ReleaseTag":
        return dataclasses.replace(self, phase=self.phase, number=self.number + 1)

    def next_phase(self) -> Optional["ReleaseTag"]:
        if self.phase in [
            RELEASE_PHASE_POST,
            RELEASE_PHASE_RC,
            RELEASE_PHASE_REV,
            RELEASE_PHASE_DEV,
        ]:
            return None

        if self.phase == RELEASE_PHASE_ALPHA:
            _phase = RELEASE_PHASE_BETA
        elif self.phase == RELEASE_PHASE_BETA:
            _phase = RELEASE_PHASE_RC
        else:
            return None

        return self.__class__(phase=_phase, number=0)


LocalSegmentType = Optional[Union[str, int, Tuple[Union[str, int], ...]]]
