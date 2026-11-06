from __future__ import annotations

from contextlib import suppress
from functools import cached_property
from typing import TYPE_CHECKING

from poetry.core.constraints.version.empty_constraint import EmptyConstraint
from poetry.core.constraints.version.version_constraint import _is_wildcard_candidate
from poetry.core.constraints.version.version_constraint import (
    _single_wildcard_range_string,
)
from poetry.core.constraints.version.version_range_constraint import (
    VersionRangeConstraint,
)
from poetry.core.constraints.version.version_union import VersionUnion


if TYPE_CHECKING:
    from poetry.core.constraints.version.version import Version
    from poetry.core.constraints.version.version_constraint import VersionConstraint


def _is_canonical_strict_max(version: Version) -> bool:
    """True if ``version`` is the dev0 of a stable release — i.e., the
    canonical exclusive upper bound that the parser produces for a
    user-typed ``<V`` (with V stable).  See ``parser._canonical_strict_max``.
    """
    if version.dev is None or version.dev.number != 0:
        return False
    return not version.without_devrelease().is_unstable()


def _display_max_text(max_: Version, include_max: bool) -> str:
    if not include_max and _is_canonical_strict_max(max_):
        return max_.without_devrelease().text
    return max_.text


def _format_upper_bound(
    max_: Version, include_max: bool, *, preserve_raw: bool = False
) -> str:
    if include_max:
        return f"<={max_.text}"
    if preserve_raw:
        return f"<={max_.text},!={max_.text}"
    return f"<{_display_max_text(max_, include_max)}"


def _range_or_empty(
    min: Version | None = None,
    max: Version | None = None,
    include_min: bool = False,
    include_max: bool = False,
) -> VersionConstraint:
    """Simplify empty ranges and ranges equivalent to ``==V``."""
    range_ = VersionRange(min, max, include_min, include_max)
    if range_.is_empty():
        return EmptyConstraint()
    if min is not None and max is not None and include_min:
        if max == min and include_max:
            return min
        if not min.is_local() and range_.normalized_upper_bound() == (
            min.next_public_version,
            False,
        ):
            return min
    return range_


class VersionRange(VersionRangeConstraint):
    def __init__(
        self,
        min: Version | None = None,
        max: Version | None = None,
        include_min: bool = False,
        include_max: bool = False,
    ) -> None:
        self._max = max
        self._min = min
        self._include_min = include_min
        self._include_max = include_max

    @property
    def min(self) -> Version | None:
        return self._min

    @property
    def max(self) -> Version | None:
        return self._max

    @property
    def include_min(self) -> bool:
        return self._include_min

    @property
    def include_max(self) -> bool:
        return self._include_max

    def is_empty(self) -> bool:
        if self._min is None or self._max is None:
            return False
        min_, include_min = self.normalized_lower_bound()
        max_, include_max = self.normalized_upper_bound()
        assert min_ is not None
        assert max_ is not None
        if min_ == max_:
            return not (include_min and include_max)
        return not self._allows_min(max_)

    def is_any(self) -> bool:
        return self._min is None and self._max is None

    def is_simple(self) -> bool:
        return self._min is None or self._max is None

    def allows(self, other: Version) -> bool:
        if not self._allows_min(other):
            return False

        if self.max is not None:
            _this, _other = self.max, other

            assert _this is not None

            if not _this.is_local() and _other.is_local():
                # allow weak equality to allow `3.0.0+local.1` for `<=3.0.0`
                _other = _other.without_local()

            if _other > _this:
                return False

            if not self._include_max and (_other == self._max or _other == _this):
                return False

        return True

    def allows_any(self, other: VersionConstraint) -> bool:
        from poetry.core.constraints.version.version import Version

        if other.is_empty():
            return False

        if isinstance(other, Version):
            if self.allows(other):
                return True

            # Although `>=1.2.3+local` does not allow the exact version `1.2.3`, both of
            # those versions do allow `1.2.3+local`.
            return (
                self.min is not None and self.min.is_local() and other.allows(self.min)
            )

        if isinstance(other, VersionUnion):
            return any(self.allows_any(constraint) for constraint in other.ranges)

        if isinstance(other, VersionRangeConstraint):
            return not (other.is_strictly_lower(self) or other.is_strictly_higher(self))

        raise ValueError(f"Unknown VersionConstraint type {other}.")

    def intersect(self, other: VersionConstraint) -> VersionConstraint:
        from poetry.core.constraints.version.version import Version

        if other.is_empty():
            return EmptyConstraint()

        if isinstance(other, VersionUnion):
            return other.intersect(self)

        if isinstance(other, Version):
            if self.allows_all(other):
                return other
            if not self.allows_any(other):
                return EmptyConstraint()
            return self.intersect(other.to_range())

        if not isinstance(other, VersionRangeConstraint):
            raise TypeError(f"Unknown VersionConstraint type {other}.")

        if self.allows_lower(other):
            if self.is_strictly_lower(other):
                return EmptyConstraint()

            intersect_min = other.min
            intersect_include_min = other.include_min
        else:
            if other.is_strictly_lower(self):
                return EmptyConstraint()

            intersect_min = self._min
            intersect_include_min = self._include_min

        if self.allows_higher(other):
            intersect_max = other.max
            intersect_include_max = other.include_max
        else:
            intersect_max = self._max
            intersect_include_max = self._include_max

        if intersect_min is None and intersect_max is None:
            return VersionRange()

        # If the range is just a single version.
        if intersect_min == intersect_max:
            # Because we already verified that the lower range isn't strictly
            # lower, there must be some overlap.
            assert intersect_include_min and intersect_include_max
            assert intersect_min is not None

            return intersect_min

        # If we got here, there is an actual range.
        return _range_or_empty(
            intersect_min, intersect_max, intersect_include_min, intersect_include_max
        )

    def union(self, other: VersionConstraint) -> VersionConstraint:
        if isinstance(other, VersionRangeConstraint):
            if self.allows_all(other):
                return self

            # If the two ranges don't overlap, we won't be able to create a single
            # VersionRange for both of them.
            edges_touch = self.is_adjacent_to(other) or other.is_adjacent_to(self)

            if not edges_touch and not self.allows_any(other):
                return VersionUnion.of(self, other)

            if self.allows_lower(other):
                union_min = self.min
                union_include_min = self.include_min
            else:
                union_min = other.min
                union_include_min = other.include_min

            if self.allows_higher(other):
                union_max = self.max
                union_include_max = self.include_max
            else:
                union_max = other.max
                union_include_max = other.include_max

            return _range_or_empty(
                union_min,
                union_max,
                include_min=union_include_min,
                include_max=union_include_max,
            )

        return VersionUnion.of(self, other)

    def difference(self, other: VersionConstraint) -> VersionConstraint:
        from poetry.core.constraints.version.version import Version

        if other.is_empty():
            return self

        if isinstance(other, Version):
            if not self.allows_any(other):
                return self
            return self.difference(other.to_range())
        elif isinstance(other, VersionRangeConstraint):
            if not self.allows_any(other):
                return self

            before: VersionConstraint | None
            if not self.allows_lower(other):
                before = None
            else:
                before = _range_or_empty(
                    self.min, other.min, self.include_min, not other.include_min
                )

            after: VersionConstraint | None
            if not self.allows_higher(other):
                after = None
            else:
                other_max, other_include_max = other.normalized_upper_bound()
                after = _range_or_empty(
                    other_max, self.max, not other_include_max, self.include_max
                )

            if before is None and after is None:
                return EmptyConstraint()

            if before is None:
                assert after is not None
                return after

            if after is None:
                return before

            return VersionUnion.of(before, after)
        elif isinstance(other, VersionUnion):
            ranges: list[VersionRangeConstraint] = []
            current: VersionRangeConstraint = self

            for range in other.ranges:
                # Skip any ranges that are strictly lower than [current].
                if range.is_strictly_lower(current):
                    continue

                # If we reach a range strictly higher than [current], no more ranges
                # will be relevant so we can bail early.
                if range.is_strictly_higher(current):
                    break

                difference = current.difference(range)
                if difference.is_empty():
                    return EmptyConstraint()
                elif isinstance(difference, VersionUnion):
                    # If [range] split [current] in half, we only need to continue
                    # checking future ranges against the latter half.
                    ranges.append(difference.ranges[0])
                    current = difference.ranges[-1]
                else:
                    assert isinstance(difference, VersionRangeConstraint)
                    current = difference

            if not ranges:
                return current

            return VersionUnion.of(*([*ranges, current]))

        raise ValueError(f"Unknown VersionConstraint type {other}.")

    def flatten(self) -> list[VersionRangeConstraint]:
        return [self]

    @cached_property
    def _single_wildcard_range_string(self) -> str:
        if not self.is_single_wildcard_range:
            raise ValueError("Not a valid wildcard range")

        assert self.min is not None
        assert self.max is not None
        return f"=={_single_wildcard_range_string(self.min, self.max)}"

    @cached_property
    def is_single_wildcard_range(self) -> bool:
        # e.g.
        # - "1.*" equals ">=1.0.dev0, <2" (equivalent to ">=1.0.dev0, <2.0.dev0")
        # - "1.0.*" equals ">=1.0.dev0, <1.1"
        # - "1.2.*" equals ">=1.2.dev0, <1.3"
        if (
            self.min is None
            or self.max is None
            or not self.include_min
            or self.include_max
        ):
            return False

        return _is_wildcard_candidate(self.min, self.max)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VersionRangeConstraint):
            return False

        return (
            self._min == other.min
            and self._max == other.max
            and self._include_min == other.include_min
            and self._include_max == other.include_max
        )

    def __lt__(self, other: VersionRangeConstraint) -> bool:
        return self._cmp(other) < 0

    def __le__(self, other: VersionRangeConstraint) -> bool:
        return self._cmp(other) <= 0

    def __gt__(self, other: VersionRangeConstraint) -> bool:
        return self._cmp(other) > 0

    def __ge__(self, other: VersionRangeConstraint) -> bool:
        return self._cmp(other) >= 0

    def _cmp(self, other: VersionRangeConstraint) -> int:
        if self.allows_lower(other):
            return -1
        if other.allows_lower(self):
            return 1

        return self._compare_max(other)

    def _compare_max(self, other: VersionRangeConstraint) -> int:
        if self.allows_higher(other):
            return 1
        if other.allows_higher(self):
            return -1
        return 0

    def __repr__(self) -> str:
        text = ""

        if self.min is not None:
            text += ">=" if self.include_min else ">"
            text += self.min.text

        if self.max is not None:
            if self.min is not None:
                text += ","

            op = "<=" if self.include_max else "<"
            # In contrast to __str__, we want to display the actual max so that
            # we can distinguish between `< 1` and `< 1.dev0` in test output.
            text += f"{op}{self.max}"

        if self.min is None and self.max is None:
            return "*"

        return f"<{self.__class__.__name__} {text}>"

    def __str__(self) -> str:
        with suppress(ValueError):
            return self._single_wildcard_range_string

        text = ""

        if self.min is not None:
            text += ">=" if self.include_min else ">"
            text += self.min.text

        if self.max is not None:
            if self.min is not None:
                text += ","

            text += _format_upper_bound(self.max, self.include_max)

        if self.min is None and self.max is None:
            return "*"

        return text

    def __hash__(self) -> int:
        return (
            hash(self.min)
            ^ hash(self.max)
            ^ hash(self.include_min)
            ^ hash(self.include_max)
        )
