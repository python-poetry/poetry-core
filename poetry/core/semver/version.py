import dataclasses

from typing import TYPE_CHECKING
from typing import Optional
from typing import Tuple
from typing import Union

from poetry.core.semver.empty_constraint import EmptyConstraint
from poetry.core.semver.version_range_constraint import VersionRangeConstraint
from poetry.core.semver.version_union import VersionUnion
from poetry.core.version.pep440 import Release
from poetry.core.version.pep440 import ReleaseTag
from poetry.core.version.pep440.version import PEP440Version


if TYPE_CHECKING:
    from poetry.core.semver.helpers import VersionTypes
    from poetry.core.version.pep440 import LocalSegmentType


@dataclasses.dataclass(frozen=True)
class Version(PEP440Version, VersionRangeConstraint):
    """
    A parsed semantic version number.
    """

    @property
    def precision(self) -> int:
        return self.release.precision

    @property
    def stable(self) -> "Version":
        if self.is_stable():
            return self

        return self.next_patch()

    def next_breaking(self) -> "Version":
        if self.major == 0:
            if self.minor != 0:
                return self.next_minor()

            if self.precision == 1:
                return self.next_major()
            elif self.precision == 2:
                return self.next_minor()

            return self.next_patch()

        return self.stable.next_major()

    def first_pre_release(self) -> "Version":
        return self.__class__(release=self.release, pre=ReleaseTag("alpha"))

    @property
    def min(self) -> "Version":
        return self

    @property
    def max(self) -> "Version":
        return self

    @property
    def full_max(self) -> "Version":
        return self

    @property
    def include_min(self) -> bool:
        return True

    @property
    def include_max(self) -> bool:
        return True

    def is_any(self) -> bool:
        return False

    def is_empty(self) -> bool:
        return False

    def allows(self, version: "Version") -> bool:
        if version is None:
            return False

        _this, _other = self, version

        # allow weak equality to allow `3.0.0+local.1` for `3.0.0`
        if not _this.is_local() and _other.is_local():
            _other = _other.without_local()
        elif _this.is_local() and not _other.is_local():
            _this = _this.without_local()

        # allow weak equality to allow `3.0.0-1` for `3.0.0`
        if not _this.is_postrelease() and _other.is_postrelease():
            _other = _other.without_postrelease()
        elif _this.without_postrelease() and not _other.without_postrelease():
            _this = _this.without_postrelease()

        return _this == _other

    def allows_all(self, other: "VersionTypes") -> bool:
        return other.is_empty() or (
            self.allows(other) if isinstance(other, self.__class__) else other == self
        )

    def allows_any(self, other: "VersionTypes") -> bool:
        return other.allows(self)

    def intersect(self, other: "VersionTypes") -> Union["Version", EmptyConstraint]:
        if other.allows(self):
            return self

        return EmptyConstraint()

    def union(self, other: "VersionTypes") -> "VersionTypes":
        from poetry.core.semver.version_range import VersionRange

        if other.allows(self):
            return other

        if isinstance(other, VersionRangeConstraint):
            if self.allows(other.min):
                return VersionRange(
                    other.min,
                    other.max,
                    include_min=True,
                    include_max=other.include_max,
                )

            if self.allows(other.max):
                return VersionRange(
                    other.min,
                    other.max,
                    include_min=other.include_min,
                    include_max=True,
                )

        return VersionUnion.of(self, other)

    def difference(self, other: "VersionTypes") -> Union["Version", EmptyConstraint]:
        if other.allows(self):
            return EmptyConstraint()

        return self

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return "<Version {}>".format(str(self))

    def __eq__(self, other: Union["Version", "VersionRangeConstraint"]) -> bool:
        from poetry.core.semver.version_range import VersionRange

        if isinstance(other, VersionRange):
            return (
                self == other.min
                and self == other.max
                and (other.include_min or other.include_max)
            )
        return super().__eq__(other)

    @classmethod
    def from_parts(
        cls,
        major: int,
        minor: Optional[int] = None,
        patch: Optional[int] = None,
        extra: Optional[Union[int, Tuple[int, ...]]] = None,
        pre: Optional[ReleaseTag] = None,
        post: Optional[ReleaseTag] = None,
        dev: Optional[ReleaseTag] = None,
        local: "LocalSegmentType" = None,
    ):
        return cls(
            release=Release(major=major, minor=minor, patch=patch, extra=extra),
            pre=pre,
            post=post,
            dev=dev,
            local=local,
        )
