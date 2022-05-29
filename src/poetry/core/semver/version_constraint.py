from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from poetry.core.semver.version import Version
    from poetry.core.semver.version_range_constraint import VersionRangeConstraint


class VersionConstraint:
    @abstractmethod
    def is_empty(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def is_any(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def is_simple(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def allows(self, version: Version) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def allows_all(self, other: VersionConstraint) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def allows_any(self, other: VersionConstraint) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def intersect(self, other: VersionConstraint) -> VersionConstraint:
        raise NotImplementedError()

    @abstractmethod
    def union(self, other: VersionConstraint) -> VersionConstraint:
        raise NotImplementedError()

    @abstractmethod
    def difference(self, other: VersionConstraint) -> VersionConstraint:
        raise NotImplementedError()

    @abstractmethod
    def flatten(self) -> list[VersionRangeConstraint]:
        raise NotImplementedError()
