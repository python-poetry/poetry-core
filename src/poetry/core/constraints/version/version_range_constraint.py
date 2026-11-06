from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from poetry.core.constraints.version.version_constraint import VersionConstraint


if TYPE_CHECKING:
    from poetry.core.constraints.version.version import Version


class VersionRangeConstraint(VersionConstraint):
    @property
    @abstractmethod
    def min(self) -> Version | None:
        raise NotImplementedError

    @property
    @abstractmethod
    def max(self) -> Version | None:
        raise NotImplementedError

    @property
    @abstractmethod
    def include_min(self) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def include_max(self) -> bool:
        raise NotImplementedError

    @property
    def allowed_min(self) -> Version | None:
        # Exclusive comparisons can exclude an unbounded post/local family.
        # The raw bound alone cannot express this; see _allows_min.
        return self.min

    def normalized_upper_bound(self) -> tuple[Version | None, bool]:
        """Return the endpoint including a public maximum's local variants."""
        max_ = self.max
        if max_ is not None and self.include_max and not max_.is_local():
            return max_.next_public_version, False
        return max_, self.include_max

    def normalized_lower_bound(self) -> tuple[Version | None, bool]:
        """Move strict dev/post bounds past the version and its local variants."""
        min_ = self.min
        if (
            min_ is not None
            and not self.include_min
            and not min_.is_local()
            and (min_.is_devrelease() or min_.is_postrelease())
        ):
            return min_.next_public_version, True
        return min_, self.include_min

    def has_upper_bound(self) -> bool:
        return self.max is not None

    def _allows_min(self, version: Version) -> bool:
        """Whether a version satisfies the lower bound."""
        min_ = self.min
        if min_ is None:
            return True
        if version < min_:
            return False
        if self.include_min:
            return True
        if version == min_:
            return False
        if min_.is_local():
            return True
        if not min_.is_postrelease() and version.is_postrelease():
            version = version.without_postrelease()
        if version.is_local():
            version = version.without_local()
        return version != min_

    def allows_all(self, other: VersionConstraint) -> bool:
        from poetry.core.constraints.version.version import Version

        if other.is_empty():
            return True

        if isinstance(other, Version):
            if not self.allows(other):
                return False

            if other.is_local():
                return True

            # An upper bound like 1+cpu excludes 1+zzz, even though it allows 1.
            max_ = self.max
            return not (
                max_ is not None and max_.is_local() and max_.without_local() == other
            )

        from poetry.core.constraints.version.version_union import VersionUnion

        if isinstance(other, VersionUnion):
            return all(self.allows_all(constraint) for constraint in other.ranges)

        if isinstance(other, VersionRangeConstraint):
            return not other.allows_lower(self) and not other.allows_higher(self)

        raise ValueError(f"Unknown VersionConstraint type {other}.")

    def allows_lower(self, other: VersionRangeConstraint) -> bool:
        _this, include_this = self.normalized_lower_bound()
        _other, include_other = other.normalized_lower_bound()

        if _this is None:
            return _other is not None

        if _other is None:
            return False

        if _this < _other:
            return self._allows_min(_other)

        if _this > _other:
            return not other._allows_min(_this)

        return include_this and not include_other

    def allows_higher(self, other: VersionRangeConstraint) -> bool:
        _this, include_this = self.normalized_upper_bound()
        _other, include_other = other.normalized_upper_bound()

        if _this is None:
            return _other is not None

        if _other is None:
            return False

        if _this < _other:
            return False

        if _this > _other:
            return True

        return include_this and not include_other

    def is_strictly_lower(self, other: VersionRangeConstraint) -> bool:
        _this, include_this = self.normalized_upper_bound()
        _other, include_other = other.normalized_lower_bound()

        if _this is None or _other is None:
            return False

        if _this == _other:
            return not (include_this and include_other)
        return not other._allows_min(_this)

    def is_strictly_higher(self, other: VersionRangeConstraint) -> bool:
        return other.is_strictly_lower(self)

    def is_adjacent_to(self, other: VersionRangeConstraint) -> bool:
        if self.max is None or other.min is None:
            return False
        max_, include_max = self.normalized_upper_bound()
        min_, include_min = other.normalized_lower_bound()
        return max_ == min_ and include_max != include_min

    def excludes_single_version_before(self, other: VersionRangeConstraint) -> bool:
        if self.max is None or self.include_max:
            return False
        if self.max.is_local():
            return self.max == other.min and not other.include_min
        return other.include_min and self.max.next_public_version == other.min
