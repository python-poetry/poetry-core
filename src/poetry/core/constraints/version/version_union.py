from __future__ import annotations

import operator as op

from functools import cached_property
from functools import reduce
from itertools import pairwise
from typing import TYPE_CHECKING

from poetry.core.constraints.version.empty_constraint import EmptyConstraint
from poetry.core.constraints.version.version_constraint import VersionConstraint
from poetry.core.constraints.version.version_constraint import _is_wildcard_candidate
from poetry.core.constraints.version.version_constraint import (
    _single_wildcard_range_string,
)
from poetry.core.constraints.version.version_range_constraint import (
    VersionRangeConstraint,
)


if TYPE_CHECKING:
    from poetry.core.constraints.version.version import Version


def _render_punctured_range(group: list[VersionRangeConstraint]) -> str:
    """Render a contiguous run of pieces sharing single-point puncture
    seams as a punctured range ``>=A,!=V1,!=V2,<B``.  Singleton runs
    defer to ``str``."""
    if len(group) == 1:
        return str(group[0])
    from poetry.core.constraints.version.version_range import _display_max_text

    first, last = group[0], group[-1]
    parts: list[str] = []
    if first.min is not None:
        parts.append(f"{'>=' if first.include_min else '>'}{first.min.text}")
    for r in group[:-1]:
        assert r.max is not None  # by construction: r is not the last piece
        parts.append(f"!={r.max.text}")
    if last.max is not None:
        max_op = "<=" if last.include_max else "<"
        parts.append(f"{max_op}{_display_max_text(last.max, last.include_max)}")
    return ",".join(parts)


class VersionUnion(VersionConstraint):
    """
    A version constraint representing a union of multiple disjoint version
    ranges.

    An instance of this will only be created if the version can't be represented
    as a non-compound value.
    """

    def __init__(self, *ranges: VersionRangeConstraint) -> None:
        self._ranges = list(ranges)

    @property
    def ranges(self) -> list[VersionRangeConstraint]:
        return self._ranges

    @classmethod
    def of(cls, *ranges: VersionConstraint) -> VersionConstraint:
        from poetry.core.constraints.version.version_range import VersionRange

        flattened: list[VersionRangeConstraint] = []
        for constraint in ranges:
            if constraint.is_empty():
                continue

            if isinstance(constraint, VersionUnion):
                flattened += constraint.ranges
                continue

            assert isinstance(constraint, VersionRangeConstraint)
            flattened.append(constraint)

        if not flattened:
            return EmptyConstraint()

        if any(constraint.is_any() for constraint in flattened):
            return VersionRange()

        # Only allow Versions and VersionRanges here so we can more easily reason
        # about everything in flattened. _EmptyVersions and VersionUnions are
        # filtered out above.
        for constraint in flattened:
            if not isinstance(constraint, VersionRangeConstraint):
                raise TypeError(f"Unknown VersionConstraint type {constraint}.")

        flattened.sort()  # type: ignore[call-arg]

        merged: list[VersionRangeConstraint] = []
        for constraint in flattened:
            # Merge this constraint with the previous one, but only if they touch.
            if not merged or (
                not merged[-1].allows_any(constraint)
                and not merged[-1].is_adjacent_to(constraint)
            ):
                merged.append(constraint)
            else:
                new_constraint = merged[-1].union(constraint)
                assert isinstance(new_constraint, VersionRangeConstraint)
                merged[-1] = new_constraint

        if len(merged) == 1:
            return merged[0]

        return VersionUnion(*merged)

    def is_empty(self) -> bool:
        return False

    def is_any(self) -> bool:
        return False

    def is_simple(self) -> bool:
        return self.excludes_single_version

    def has_upper_bound(self) -> bool:
        return all(constraint.has_upper_bound() for constraint in self._ranges)

    def allows(self, version: Version) -> bool:
        if self.excludes_single_version:
            return not self._excluded_single_version.allows(version)

        return any(
            constraint.allows(version) for constraint in self._ranges
        ) or self._allowed_at_puncture(version)

    def _allowed_at_puncture(self, version: Version) -> bool:
        """Allow pre/dev/post variants at a single-point puncture seam.

        Adjacent pieces ``<V`` / ``>V`` with raw exclusive bounds exclude
        only ``V`` itself (see ``_union_string``).  The right-hand piece is
        spelled like the exclusive ordered comparison ``>V``, whose PEP 440
        semantics strip post-releases of ``V`` before comparing, so a
        post-release such as ``V.post1`` is wrongly rejected by the piece
        even though it is not ``V``.  Rescue such variants of the seam
        version here, as long as they lie within the outer bounds of the
        seam pieces.  Pure local variants of ``V`` stay excluded, matching
        the point semantics of ``!=V`` (``packaging`` agrees).
        """
        for prev, cur in pairwise(self._ranges):
            if (
                prev.max is None
                or prev.max != cur.min
                or prev.include_max
                or cur.include_min
            ):
                continue
            seam = prev.max
            if seam.allows(version):
                # the excluded point itself (or a pure local variant of it)
                continue
            if version.post is None or seam.post is not None:
                # Only the post-release family of the seam version itself is
                # wrongly rejected by the ``>V`` piece; pre/dev variants of
                # ``V`` are already allowed by the ``<V`` piece, and a seam at
                # a post-release excludes nothing extra.
                continue
            base = version.without_postrelease()
            if base.is_local():
                base = base.without_local()
            if base != seam:
                continue
            if prev.min is not None and (
                version < prev.min or (not prev.include_min and version == prev.min)
            ):
                continue
            if cur.max is not None and (
                version > cur.max or (not cur.include_max and version == cur.max)
            ):
                continue
            return True

        return False

    def allows_all(self, other: VersionConstraint) -> bool:
        from poetry.core.constraints.version.version import Version

        if isinstance(other, Version):
            if not self.allows(other):
                return False

            if other.is_local():
                # `==1.2.3+local` allows nothing but that very version.
                return True

            # A public version is fully allowed only if every local variant
            # of it is allowed, too.  A bound that is a local variant of
            # `other` splits that band (mirrors VersionRange.allows_all).
            return not any(
                r.max is not None
                and r.max.is_local()
                and r.max.without_local() == other
                and (r.min is None or r.min <= other)
                for r in self._ranges
            )

        our_ranges = iter(self._ranges)
        their_ranges = iter(other.flatten())

        our_current_range = next(our_ranges, None)
        their_current_range = next(their_ranges, None)

        while our_current_range and their_current_range:
            if our_current_range.allows_all(their_current_range):
                their_current_range = next(their_ranges, None)
            else:
                our_current_range = next(our_ranges, None)

        return their_current_range is None

    def allows_any(self, other: VersionConstraint) -> bool:
        from poetry.core.constraints.version.version import Version

        if isinstance(other, Version) and self.allows(other):
            return True

        our_ranges = iter(self._ranges)
        their_ranges = iter(other.flatten())

        our_current_range = next(our_ranges, None)
        their_current_range = next(their_ranges, None)

        while our_current_range and their_current_range:
            if our_current_range.allows_any(their_current_range):
                return True

            if their_current_range.allows_higher(our_current_range):
                our_current_range = next(our_ranges, None)
            else:
                their_current_range = next(their_ranges, None)

        return False

    def intersect(self, other: VersionConstraint) -> VersionConstraint:
        from poetry.core.constraints.version.version import Version

        if isinstance(other, Version) and self.allows(other):
            # A single point inside the union intersects to the point itself;
            # the pairwise walk below would lose variants rescued at a
            # puncture seam.
            return other

        our_ranges = iter(self._ranges)
        their_ranges = iter(other.flatten())
        new_ranges = []

        our_current_range = next(our_ranges, None)
        their_current_range = next(their_ranges, None)

        while our_current_range and their_current_range:
            intersection = our_current_range.intersect(their_current_range)

            if not intersection.is_empty():
                new_ranges.append(intersection)

            if their_current_range.allows_higher(our_current_range):
                our_current_range = next(our_ranges, None)
            else:
                their_current_range = next(their_ranges, None)

        return VersionUnion.of(*new_ranges)

    def union(self, other: VersionConstraint) -> VersionConstraint:
        return VersionUnion.of(self, other)

    def difference(self, other: VersionConstraint) -> VersionConstraint:
        from poetry.core.constraints.version.version import Version

        if isinstance(other, Version) and self.allows(other):
            # Removing a single point splits the containing piece (or the
            # pieces around a puncture seam) at that point; express the
            # complement of the point as ranges and let the comparison-based
            # walk do the split.
            from poetry.core.constraints.version.version_range import VersionRange

            return self.intersect(
                VersionUnion.of(
                    VersionRange(max=other),
                    VersionRange(min=other),
                )
            )

        our_ranges = iter(self._ranges)
        their_ranges = iter(other.flatten())
        new_ranges: list[VersionConstraint] = []

        state = {
            "current": next(our_ranges, None),
            "their_range": next(their_ranges, None),
        }

        def their_next_range() -> bool:
            state["their_range"] = next(their_ranges, None)
            if state["their_range"]:
                return True

            assert state["current"] is not None
            new_ranges.append(state["current"])
            our_current = next(our_ranges, None)
            while our_current:
                new_ranges.append(our_current)
                our_current = next(our_ranges, None)

            return False

        def our_next_range(include_current: bool = True) -> bool:
            if include_current:
                assert state["current"] is not None
                new_ranges.append(state["current"])

            our_current = next(our_ranges, None)
            if not our_current:
                return False

            state["current"] = our_current

            return True

        while True:
            if state["their_range"] is None:
                break

            assert state["current"] is not None
            if state["their_range"].is_strictly_lower(state["current"]):
                if not their_next_range():
                    break

                continue

            if state["their_range"].is_strictly_higher(state["current"]):
                if not our_next_range():
                    break

                continue

            difference = state["current"].difference(state["their_range"])
            if isinstance(difference, VersionUnion):
                assert len(difference.ranges) == 2
                new_ranges.append(difference.ranges[0])
                state["current"] = difference.ranges[-1]

                if not their_next_range():
                    break
            elif difference.is_empty():
                if not our_next_range(False):
                    break
            else:
                assert isinstance(difference, VersionRangeConstraint)
                state["current"] = difference

                if state["current"].allows_higher(state["their_range"]):
                    if not their_next_range():
                        break
                elif not our_next_range():
                    break

        if not new_ranges:
            return EmptyConstraint()

        if len(new_ranges) == 1:
            return new_ranges[0]

        return VersionUnion.of(*new_ranges)

    def flatten(self) -> list[VersionRangeConstraint]:
        return self.ranges

    @cached_property
    def _exclude_single_wildcard_range_string(self) -> str:
        """
        Helper method to convert this instance into a wild card range
        string.
        """
        if not self.excludes_single_wildcard_range:
            raise ValueError("Not a valid wildcard range")

        idx_order = (0, 1) if self._ranges[0].max else (1, 0)
        one = self._ranges[idx_order[0]]
        two = self._ranges[idx_order[1]]

        assert one.max is not None
        assert two.min is not None
        return f"!={_single_wildcard_range_string(one.max, two.min)}"

    @cached_property
    def excludes_single_wildcard_range(self) -> bool:
        if len(self._ranges) != 2:
            return False

        idx_order = (0, 1) if self._ranges[0].max else (1, 0)
        one = self._ranges[idx_order[0]]
        two = self._ranges[idx_order[1]]

        if (
            one.max is None
            or one.include_max
            or one.min is not None
            or two.min is None
            or not two.include_min
            or two.max is not None
        ):
            return False

        return _is_wildcard_candidate(two.min, one.max, inverted=True)

    @cached_property
    def excludes_single_version(self) -> bool:
        from poetry.core.constraints.version.version import Version

        return isinstance(self._inverted, Version)

    @cached_property
    def _excluded_single_version(self) -> Version:
        from poetry.core.constraints.version.version import Version

        excluded = self._inverted
        assert isinstance(excluded, Version)
        return excluded

    @cached_property
    def _inverted(self) -> VersionConstraint:
        from poetry.core.constraints.version.version_range import VersionRange

        return VersionRange().difference(self)

    @cached_property
    def _union_string(self) -> str:
        """Render the union as one or more punctured ranges joined by
        ``||``.  A punctured range is a maximal run of pieces whose
        internal seams are single-point exclusions: ``<V`` immediately
        followed by ``>V`` excludes only ``{V}`` (both bounds raw
        exclusive), so the run renders as ``>=A,!=V1,!=V2,<B``.  A seam
        ``<V.dev0`` followed by ``>V`` instead spans a whole range and
        is *not* collapsible -- ``ranges[i].max == ranges[i+1].min``
        distinguishes the two cases.

        This makes results like ``(>1).intersect(!=2)`` round-trip:
        ``>1,!=2`` re-parses to the same internal raw structure, whereas
        ``>1,<2 || >2`` would re-parse with the canonicalized ``<2.dev0``
        and yield a strictly smaller set.

        When no seam is collapsible every group is a singleton and the
        result is identical to the naive ``" || ".join(map(str, ...))``
        rendering -- so this method also handles that case directly.
        """
        # ``VersionUnion.of`` produces sorted ranges, but the bare
        # constructor doesn't enforce that, so sort defensively.
        ranges = sorted(self._ranges)  # type: ignore[type-var]

        groups: list[list[VersionRangeConstraint]] = [[ranges[0]]]
        for prev, cur in pairwise(ranges):
            # A puncture seam requires both bounds to be raw-exclusive at the
            # same Version.  Adjacent inclusive bounds would mean the seam
            # version is actually allowed by one of the pieces -- well-formed
            # unions from ``VersionUnion.of`` never produce that shape, but
            # the assertion-as-condition keeps us safe against direct
            # ``VersionUnion(...)`` construction.
            if (
                prev.max is not None
                and prev.max == cur.min
                and not prev.include_max
                and not cur.include_min
            ):
                groups[-1].append(cur)
            else:
                groups.append([cur])

        return " || ".join(_render_punctured_range(g) for g in groups)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VersionUnion):
            return False

        return self._ranges == other.ranges

    def __hash__(self) -> int:
        return reduce(op.xor, map(hash, self._ranges))

    def __str__(self) -> str:
        try:
            return self._exclude_single_wildcard_range_string
        except ValueError:
            return self._union_string
