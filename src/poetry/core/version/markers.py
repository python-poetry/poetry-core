import re

from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Union

from poetry.core.version.grammars import GRAMMAR_PEP_508_MARKERS
from poetry.core.version.parser import Parser


if TYPE_CHECKING:
    from lark import Tree

    from poetry.core.semver.helpers import VersionTypes

MarkerTypes = Union[
    "AnyMarker", "EmptyMarker", "SingleMarker", "MultiMarker", "MarkerUnion"
]


class InvalidMarker(ValueError):
    """
    An invalid marker was found, users should refer to PEP 508.
    """


class UndefinedComparison(ValueError):
    """
    An invalid operation was attempted on a value that doesn't support it.
    """


class UndefinedEnvironmentName(ValueError):
    """
    A name was attempted to be used that does not exist inside of the
    environment.
    """


ALIASES = {
    "os.name": "os_name",
    "sys.platform": "sys_platform",
    "platform.version": "platform_version",
    "platform.machine": "platform_machine",
    "platform.python_implementation": "platform_python_implementation",
    "python_implementation": "platform_python_implementation",
}

PYTHON_VERSION_MARKERS = ["python_version", "python_full_version"]

# Parser: PEP 508 Environment Markers
_parser = Parser(GRAMMAR_PEP_508_MARKERS, "lalr")


class BaseMarker:
    def intersect(self, other: "BaseMarker") -> "BaseMarker":
        raise NotImplementedError()

    def union(self, other: "BaseMarker") -> "BaseMarker":
        raise NotImplementedError()

    def is_any(self) -> bool:
        return False

    def is_empty(self) -> bool:
        return False

    def validate(self, environment: Dict[str, Any]) -> bool:
        raise NotImplementedError()

    def without_extras(self) -> "BaseMarker":
        raise NotImplementedError()

    def exclude(self, marker_name: str) -> "BaseMarker":
        raise NotImplementedError()

    def only(self, *marker_names: str) -> "BaseMarker":
        raise NotImplementedError()

    def invert(self) -> "BaseMarker":
        raise NotImplementedError()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {str(self)}>"


class AnyMarker(BaseMarker):
    def intersect(self, other: MarkerTypes) -> MarkerTypes:
        return other

    def union(self, other: MarkerTypes) -> MarkerTypes:
        return self

    def is_any(self) -> bool:
        return True

    def is_empty(self) -> bool:
        return False

    def validate(self, environment: Dict[str, Any]) -> bool:
        return True

    def without_extras(self) -> MarkerTypes:
        return self

    def exclude(self, marker_name: str) -> MarkerTypes:
        return self

    def only(self, *marker_names: str) -> MarkerTypes:
        return self

    def invert(self) -> "EmptyMarker":
        return EmptyMarker()

    def __str__(self) -> str:
        return ""

    def __repr__(self) -> str:
        return "<AnyMarker>"

    def __hash__(self) -> int:
        return hash(("<any>", "<any>"))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseMarker):
            return NotImplemented

        return isinstance(other, AnyMarker)


class EmptyMarker(BaseMarker):
    def intersect(self, other: MarkerTypes) -> MarkerTypes:
        return self

    def union(self, other: MarkerTypes) -> MarkerTypes:
        return other

    def is_any(self) -> bool:
        return False

    def is_empty(self) -> bool:
        return True

    def validate(self, environment: Dict[str, Any]) -> bool:
        return False

    def without_extras(self) -> BaseMarker:
        return self

    def exclude(self, marker_name: str) -> "EmptyMarker":
        return self

    def only(self, *marker_names: str) -> "EmptyMarker":
        return self

    def invert(self) -> AnyMarker:
        return AnyMarker()

    def __str__(self) -> str:
        return "<empty>"

    def __repr__(self) -> str:
        return "<EmptyMarker>"

    def __hash__(self) -> int:
        return hash(("<empty>", "<empty>"))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseMarker):
            return NotImplemented

        return isinstance(other, EmptyMarker)


class SingleMarker(BaseMarker):

    _CONSTRAINT_RE = re.compile(r"(?i)^(~=|!=|>=?|<=?|==?=?|in|not in)?\s*(.+)$")
    _VERSION_LIKE_MARKER_NAME = {
        "python_version",
        "python_full_version",
        "platform_release",
    }

    def __init__(self, name: str, constraint: Union[str, "VersionTypes"]) -> None:
        from poetry.core.packages.constraints import (
            parse_constraint as parse_generic_constraint,
        )
        from poetry.core.semver.helpers import parse_constraint

        self._name = ALIASES.get(name, name)
        self._constraint_string = str(constraint)

        # Extract operator and value
        m = self._CONSTRAINT_RE.match(self._constraint_string)
        self._operator = m.group(1)
        if self._operator is None:
            self._operator = "=="

        self._value = m.group(2)
        self._parser = parse_generic_constraint

        if name in self._VERSION_LIKE_MARKER_NAME:
            self._parser = parse_constraint

            if self._operator in {"in", "not in"}:
                versions = []
                for v in re.split("[ ,]+", self._value):
                    split = v.split(".")
                    if len(split) in [1, 2]:
                        split.append("*")
                        op = "" if self._operator == "in" else "!="
                    else:
                        op = "==" if self._operator == "in" else "!="

                    versions.append(op + ".".join(split))

                glue = ", "
                if self._operator == "in":
                    glue = " || "

                self._constraint = self._parser(glue.join(versions))
            else:
                self._constraint = self._parser(self._constraint_string)
        else:
            # if we have a in/not in operator we split the constraint
            # into a union/multi-constraint of single constraint
            constraint_string = self._constraint_string
            if self._operator in {"in", "not in"}:
                op, glue = ("==", " || ") if self._operator == "in" else ("!=", ", ")
                values = re.split("[ ,]+", self._value)
                constraint_string = glue.join(f"{op} {value}" for value in values)

            self._constraint = self._parser(constraint_string)

    @property
    def name(self) -> str:
        return self._name

    @property
    def constraint_string(self) -> str:
        if self._operator in {"in", "not in"}:
            return f"{self._operator} {self._value}"

        return self._constraint_string

    @property
    def constraint(self) -> "VersionTypes":
        return self._constraint

    @property
    def operator(self) -> str:
        return self._operator

    @property
    def value(self) -> str:
        return self._value

    def intersect(self, other: MarkerTypes) -> MarkerTypes:
        if isinstance(other, SingleMarker):
            return MultiMarker.of(self, other)

        return other.intersect(self)

    def union(self, other: MarkerTypes) -> MarkerTypes:
        if isinstance(other, SingleMarker):
            if self == other:
                return self

            if self == other.invert():
                return AnyMarker()

            return MarkerUnion.of(self, other)

        return other.union(self)

    def validate(self, environment: Dict[str, Any]) -> bool:
        if environment is None:
            return True

        if self._name not in environment:
            return True

        return self._constraint.allows(self._parser(environment[self._name]))

    def without_extras(self) -> MarkerTypes:
        return self.exclude("extra")

    def exclude(self, marker_name: str) -> MarkerTypes:
        if self.name == marker_name:
            return AnyMarker()

        return self

    def only(self, *marker_names: str) -> Union["SingleMarker", EmptyMarker]:
        if self.name not in marker_names:
            return EmptyMarker()

        return self

    def invert(self) -> MarkerTypes:
        if self._operator in ("===", "=="):
            operator = "!="
        elif self._operator == "!=":
            operator = "=="
        elif self._operator == ">":
            operator = "<="
        elif self._operator == ">=":
            operator = "<"
        elif self._operator == "<":
            operator = ">="
        elif self._operator == "<=":
            operator = ">"
        elif self._operator == "in":
            operator = "not in"
        elif self._operator == "not in":
            operator = "in"
        elif self._operator == "~=":
            # This one is more tricky to handle
            # since it's technically a multi marker
            # so the inverse will be a union of inverse
            from poetry.core.semver.version_range_constraint import (
                VersionRangeConstraint,
            )

            if not isinstance(self._constraint, VersionRangeConstraint):
                # The constraint must be a version range, otherwise
                # it's an internal error
                raise RuntimeError(
                    "The '~=' operator should only represent version ranges"
                )

            min_ = self._constraint.min
            min_operator = ">=" if self._constraint.include_min else "<"
            max_ = self._constraint.max
            max_operator = "<=" if self._constraint.include_max else "<"

            return MultiMarker.of(
                SingleMarker(self._name, f"{min_operator} {min_}"),
                SingleMarker(self._name, f"{max_operator} {max_}"),
            ).invert()
        else:
            # We should never go there
            raise RuntimeError(f"Invalid marker operator '{self._operator}'")

        return parse_marker(f"{self._name} {operator} '{self._value}'")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SingleMarker):
            return False

        return self._name == other.name and self._constraint == other.constraint

    def __hash__(self) -> int:
        return hash((self._name, self._constraint_string))

    def __str__(self) -> str:
        return f'{self._name} {self._operator} "{self._value}"'


def _flatten_markers(
    markers: Iterator[Union["MarkerUnion", "MultiMarker"]], flatten_class: Any
) -> List[MarkerTypes]:
    flattened = []

    for marker in markers:
        if isinstance(marker, flatten_class):
            flattened += _flatten_markers(marker.markers, flatten_class)
        else:
            flattened.append(marker)

    return flattened


class MultiMarker(BaseMarker):
    def __init__(self, *markers: MarkerTypes) -> None:
        self._markers = []

        markers = _flatten_markers(markers, MultiMarker)

        for m in markers:
            self._markers.append(m)

    @classmethod
    def of(cls, *markers: MarkerTypes) -> MarkerTypes:
        new_markers = _flatten_markers(markers, MultiMarker)
        markers = []

        while markers != new_markers:
            markers = new_markers
            new_markers = []
            for marker in markers:
                if marker in new_markers:
                    continue

                if marker.is_any():
                    continue

                if isinstance(marker, SingleMarker):
                    intersected = False
                    for i, mark in enumerate(new_markers):
                        if isinstance(mark, SingleMarker) and (
                            mark.name == marker.name
                            or (
                                mark.name in PYTHON_VERSION_MARKERS
                                and marker.name in PYTHON_VERSION_MARKERS
                            )
                        ):
                            intersection = mark.constraint.intersect(marker.constraint)
                            if intersection == mark.constraint:
                                intersected = True
                            elif intersection == marker.constraint:
                                new_markers[i] = marker
                                intersected = True
                            elif intersection.is_empty():
                                return EmptyMarker()
                        elif isinstance(mark, MarkerUnion):
                            intersection = mark.intersect(marker)
                            if isinstance(intersection, SingleMarker):
                                new_markers[i] = intersection
                            elif intersection.is_empty():
                                return EmptyMarker()
                    if intersected:
                        continue

                elif isinstance(marker, MarkerUnion):
                    for mark in new_markers:
                        if isinstance(mark, SingleMarker):
                            intersection = marker.intersect(mark)
                            if isinstance(intersection, SingleMarker):
                                marker = intersection
                                break
                            elif intersection.is_empty():
                                return EmptyMarker()

                new_markers.append(marker)

        if any(m.is_empty() for m in new_markers) or not new_markers:
            return EmptyMarker()

        if len(new_markers) == 1:
            return new_markers[0]

        return MultiMarker(*new_markers)

    @property
    def markers(self) -> List[MarkerTypes]:
        return self._markers

    def intersect(self, other: MarkerTypes) -> MarkerTypes:
        if other.is_any():
            return self

        if other.is_empty():
            return other

        new_markers = self._markers + [other]

        return MultiMarker.of(*new_markers)

    def union(self, other: MarkerTypes) -> MarkerTypes:
        if other in self._markers:
            return other

        if isinstance(other, (SingleMarker, MultiMarker)):
            return MarkerUnion.of(self, other)

        return other.union(self)

    def validate(self, environment: Dict[str, Any]) -> bool:
        return all(m.validate(environment) for m in self._markers)

    def without_extras(self) -> MarkerTypes:
        return self.exclude("extra")

    def exclude(self, marker_name: str) -> MarkerTypes:
        new_markers = []

        for m in self._markers:
            if isinstance(m, SingleMarker) and m.name == marker_name:
                # The marker is not relevant since it must be excluded
                continue

            marker = m.exclude(marker_name)

            if not marker.is_empty():
                new_markers.append(marker)

        return self.of(*new_markers)

    def only(self, *marker_names: str) -> MarkerTypes:
        new_markers = []

        for m in self._markers:
            if isinstance(m, SingleMarker) and m.name not in marker_names:
                # The marker is not relevant since it's not one we want
                continue

            marker = m.only(*marker_names)

            if not marker.is_empty():
                new_markers.append(marker)

        return self.of(*new_markers)

    def invert(self) -> MarkerTypes:
        markers = [marker.invert() for marker in self._markers]

        return MarkerUnion.of(*markers)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MultiMarker):
            return False

        return set(self._markers) == set(other.markers)

    def __hash__(self) -> int:
        h = hash("multi")
        for m in self._markers:
            h |= hash(m)

        return h

    def __str__(self) -> str:
        elements = []
        for m in self._markers:
            if isinstance(m, (SingleMarker, MultiMarker)):
                elements.append(str(m))
            else:
                elements.append(f"({str(m)})")

        return " and ".join(elements)


class MarkerUnion(BaseMarker):
    def __init__(self, *markers: MarkerTypes) -> None:
        self._markers = list(markers)

    @property
    def markers(self) -> List[MarkerTypes]:
        return self._markers

    @classmethod
    def of(cls, *markers: BaseMarker) -> MarkerTypes:
        flattened_markers = _flatten_markers(markers, MarkerUnion)

        markers = []
        for marker in flattened_markers:
            if marker in markers:
                continue

            if (
                isinstance(marker, SingleMarker)
                and marker.name in PYTHON_VERSION_MARKERS
            ):
                included = False
                for i, mark in enumerate(markers):
                    if (
                        not isinstance(mark, SingleMarker)
                        or mark.name not in PYTHON_VERSION_MARKERS
                    ):
                        continue

                    union = mark.constraint.union(marker.constraint)
                    if union == mark.constraint:
                        included = True
                        break
                    elif union == marker.constraint:
                        markers[i] = marker
                        included = True
                        break
                    elif union.is_any():
                        return AnyMarker()

                if included:
                    continue

            markers.append(marker)

        if any(m.is_any() for m in markers):
            return AnyMarker()

        if not markers:
            return EmptyMarker()

        if len(markers) == 1:
            return markers[0]

        return MarkerUnion(*markers)

    def append(self, marker: MarkerTypes) -> None:
        if marker in self._markers:
            return

        self._markers.append(marker)

    def intersect(self, other: MarkerTypes) -> MarkerTypes:
        if other.is_any():
            return self

        if other.is_empty():
            return other

        new_markers = []
        if isinstance(other, (SingleMarker, MultiMarker)):
            for marker in self._markers:
                intersection = marker.intersect(other)

                if not intersection.is_empty():
                    new_markers.append(intersection)
        elif isinstance(other, MarkerUnion):
            for our_marker in self._markers:
                for their_marker in other.markers:
                    intersection = our_marker.intersect(their_marker)

                    if not intersection.is_empty():
                        new_markers.append(intersection)

        return MarkerUnion.of(*new_markers)

    def union(self, other: MarkerTypes) -> MarkerTypes:
        if other.is_any():
            return other

        if other.is_empty():
            return self

        new_markers = self._markers + [other]

        return MarkerUnion.of(*new_markers)

    def validate(self, environment: Dict[str, Any]) -> bool:
        return any(m.validate(environment) for m in self._markers)

    def without_extras(self) -> MarkerTypes:
        return self.exclude("extra")

    def exclude(self, marker_name: str) -> MarkerTypes:
        new_markers = []

        for m in self._markers:
            if isinstance(m, SingleMarker) and m.name == marker_name:
                # The marker is not relevant since it must be excluded
                continue

            marker = m.exclude(marker_name)

            if not marker.is_empty():
                new_markers.append(marker)

        return self.of(*new_markers)

    def only(self, *marker_names: str) -> MarkerTypes:
        new_markers = []

        for m in self._markers:
            if isinstance(m, SingleMarker) and m.name not in marker_names:
                # The marker is not relevant since it's not one we want
                continue

            marker = m.only(*marker_names)

            if not marker.is_empty():
                new_markers.append(marker)

        return self.of(*new_markers)

    def invert(self) -> MarkerTypes:
        markers = [marker.invert() for marker in self._markers]

        return MultiMarker.of(*markers)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MarkerUnion):
            return False

        return set(self._markers) == set(other.markers)

    def __hash__(self) -> int:
        h = hash("union")
        for m in self._markers:
            h |= hash(m)

        return h

    def __str__(self) -> str:
        return " or ".join(
            str(m) for m in self._markers if not m.is_any() and not m.is_empty()
        )

    def is_any(self) -> bool:
        return any(m.is_any() for m in self._markers)

    def is_empty(self) -> bool:
        return all(m.is_empty() for m in self._markers)


def parse_marker(marker: str) -> MarkerTypes:
    if marker == "<empty>":
        return EmptyMarker()

    if not marker or marker == "*":
        return AnyMarker()

    parsed = _parser.parse(marker)

    markers = _compact_markers(parsed.children)

    return markers


def _compact_markers(tree_elements: "Tree", tree_prefix: str = "") -> MarkerTypes:
    from lark import Token

    groups = [MultiMarker()]
    for token in tree_elements:
        if isinstance(token, Token):
            if token.type == f"{tree_prefix}BOOL_OP" and token.value == "or":
                groups.append(MultiMarker())

            continue

        if token.data == "marker":
            groups[-1] = MultiMarker.of(
                groups[-1], _compact_markers(token.children, tree_prefix=tree_prefix)
            )
        elif token.data == f"{tree_prefix}item":
            name, op, value = token.children
            if value.type == f"{tree_prefix}MARKER_NAME":
                name, value, = (
                    value,
                    name,
                )

            value = value[1:-1]
            groups[-1] = MultiMarker.of(
                groups[-1], SingleMarker(str(name), f"{op}{value}")
            )
        elif token.data == f"{tree_prefix}BOOL_OP" and token.children[0] == "or":
            groups.append(MultiMarker())

    for i, group in enumerate(reversed(groups)):
        if group.is_empty():
            del groups[len(groups) - 1 - i]
            continue

        if isinstance(group, MultiMarker) and len(group.markers) == 1:
            groups[len(groups) - 1 - i] = group.markers[0]

    if not groups:
        return EmptyMarker()

    if len(groups) == 1:
        return groups[0]

    return MarkerUnion.of(*groups)
