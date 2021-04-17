from typing import FrozenSet
from typing import List
from typing import Optional


class PackageSpecification(object):
    def __init__(
        self,
        name: str,
        source_type: Optional[str] = None,
        source_url: Optional[str] = None,
        source_reference: Optional[str] = None,
        source_resolved_reference: Optional[str] = None,
        features: Optional[List[str]] = None,
    ):
        from poetry.core.utils.helpers import canonicalize_name

        self._pretty_name = name
        self._name = canonicalize_name(name)
        self._source_type = source_type
        self._source_url = source_url
        self._source_reference = source_reference
        self._source_resolved_reference = source_resolved_reference

        if not features:
            features = []

        self._features = frozenset(features)

    @property
    def name(self) -> str:
        return self._name

    @property
    def pretty_name(self) -> str:
        return self._pretty_name

    @property
    def complete_name(self) -> str:
        name = self._name

        if self._features:
            name = "{}[{}]".format(name, ",".join(sorted(self._features)))

        return name

    @property
    def source_type(self) -> Optional[str]:
        return self._source_type

    @property
    def source_url(self) -> Optional[str]:
        return self._source_url

    @property
    def source_reference(self) -> Optional[str]:
        return self._source_reference

    @property
    def source_resolved_reference(self) -> Optional[str]:
        return self._source_resolved_reference

    @property
    def features(self) -> FrozenSet[str]:
        return self._features

    def is_same_package_as(self, other: "PackageSpecification") -> bool:
        if other.complete_name != self.complete_name:
            return False

        if self._source_type:
            if self._source_type != other.source_type:
                return False

            if self._source_url or other.source_url:
                if self._source_url != other.source_url:
                    return False

            if self._source_reference or other.source_reference:
                # special handling for packages with references
                if not self._source_reference or not other.source_reference:
                    # case: one reference is defined and is non-empty, but other is not
                    return False

                if not (
                    self._source_reference == other.source_reference
                    or self._source_reference.startswith(other.source_reference)
                    or other.source_reference.startswith(self._source_reference)
                ):
                    # case: both references defined, but one is not equal to or a short
                    # representation of the other
                    return False

                if (
                    self._source_resolved_reference
                    and other.source_resolved_reference
                    and self._source_resolved_reference
                    != other.source_resolved_reference
                ):
                    return False

        return True

    def __hash__(self) -> int:
        if not self._source_type:
            return hash(self._name)

        return (
            hash(self._name)
            ^ hash(self._source_type)
            ^ hash(self._source_url)
            ^ hash(self._source_reference)
            ^ hash(self._source_resolved_reference)
            ^ hash(self._features)
        )

    def __str__(self) -> str:
        raise NotImplementedError()
