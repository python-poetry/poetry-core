import re

from typing import TYPE_CHECKING
from typing import Union


if TYPE_CHECKING:
    from .empty_constraint import EmptyConstraint  # noqa
    from .version import Version  # noqa
    from .version_range import VersionRange  # noqa
    from .version_union import VersionUnion  # noqa


VersionTypes = Union["Version", "VersionRange", "VersionUnion", "EmptyConstraint"]


def parse_constraint(constraints: str) -> VersionTypes:
    if constraints == "*":
        from .version_range import VersionRange

        return VersionRange()

    or_constraints = re.split(r"\s*\|\|?\s*", constraints.strip())
    or_groups = []
    for constraints in or_constraints:
        and_constraints = re.split(
            "(?<!^)(?<![~=>< ,]) *(?<!-)[, ](?!-) *(?!,|$)", constraints
        )
        constraint_objects = []

        if len(and_constraints) > 1:
            for constraint in and_constraints:
                constraint_objects.append(parse_single_constraint(constraint))
        else:
            constraint_objects.append(parse_single_constraint(and_constraints[0]))

        if len(constraint_objects) == 1:
            constraint = constraint_objects[0]
        else:
            constraint = constraint_objects[0]
            for next_constraint in constraint_objects[1:]:
                constraint = constraint.intersect(next_constraint)

        or_groups.append(constraint)

    if len(or_groups) == 1:
        return or_groups[0]
    else:
        from .version_union import VersionUnion

        return VersionUnion.of(*or_groups)


def parse_single_constraint(constraint: str) -> VersionTypes:
    from .patterns import BASIC_CONSTRAINT
    from .patterns import CARET_CONSTRAINT
    from .patterns import TILDE_CONSTRAINT
    from .patterns import TILDE_PEP440_CONSTRAINT
    from .patterns import X_CONSTRAINT
    from .version import Version
    from .version_range import VersionRange
    from .version_union import VersionUnion

    m = re.match(r"(?i)^v?[xX*](\.[xX*])*$", constraint)
    if m:
        return VersionRange()

    # Tilde range
    m = TILDE_CONSTRAINT.match(constraint)
    if m:
        version = Version.parse(m.group(1))
        high = version.stable.next_minor()
        if len(m.group(1).split(".")) == 1:
            high = version.stable.next_major()

        return VersionRange(version, high, include_min=True)

    # PEP 440 Tilde range (~=)
    m = TILDE_PEP440_CONSTRAINT.match(constraint)
    if m:
        precision = 1
        if m.group(3):
            precision += 1

            if m.group(4):
                precision += 1

        version = Version.parse(m.group(1))

        if precision == 2:
            high = version.stable.next_major()
        else:
            high = version.stable.next_minor()

        return VersionRange(version, high, include_min=True)

    # Caret range
    m = CARET_CONSTRAINT.match(constraint)
    if m:
        version = Version.parse(m.group(1))

        return VersionRange(version, version.next_breaking(), include_min=True)

    # X Range
    m = X_CONSTRAINT.match(constraint)
    if m:
        op = m.group(1)
        major = int(m.group(2))
        minor = m.group(3)

        if minor is not None:
            version = Version.from_parts(major, int(minor), 0)
            result = VersionRange(version, version.next_minor(), include_min=True)
        else:
            if major == 0:
                result = VersionRange(max=Version.from_parts(1, 0, 0))
            else:
                version = Version.from_parts(major, 0, 0)

                result = VersionRange(version, version.next_major(), include_min=True)

        if op == "!=":
            result = VersionRange().difference(result)

        return result

    # Basic comparator
    m = BASIC_CONSTRAINT.match(constraint)
    if m:
        op = m.group(1)
        version = m.group(2)

        # Technically invalid constraints like `>= 3.*` will appear
        # here as `3.`.
        # Pip currently supports these and to avoid breaking existing
        # users workflows we need to support them as well. To do so,
        # we just remove the inconsequential part.
        version = version.rstrip(".")

        if version == "dev":
            version = "0.0-dev"

        try:
            version = Version.parse(version)
        except ValueError:
            raise ValueError(f"Could not parse version constraint: {constraint}")

        if op == "<":
            return VersionRange(max=version)
        elif op == "<=":
            return VersionRange(max=version, include_max=True)
        elif op == ">":
            return VersionRange(min=version)
        elif op == ">=":
            return VersionRange(min=version, include_min=True)
        elif op == "!=":
            return VersionUnion(VersionRange(max=version), VersionRange(min=version))
        else:
            return version

    from .exceptions import ParseConstraintError

    raise ParseConstraintError(f"Could not parse version constraint: {constraint}")
