from __future__ import annotations

import re

from poetry.core.packages.constraints.any_constraint import AnyConstraint
from poetry.core.packages.constraints.base_constraint import BaseConstraint
from poetry.core.packages.constraints.constraint import Constraint
from poetry.core.packages.constraints.empty_constraint import EmptyConstraint
from poetry.core.packages.constraints.multi_constraint import MultiConstraint
from poetry.core.packages.constraints.union_constraint import UnionConstraint


BASIC_CONSTRAINT = re.compile(r"^(!?==?)?\s*([^\s]+?)\s*$")


def parse_constraint(constraints: str) -> BaseConstraint:
    if constraints == "*":
        return AnyConstraint()

    or_constraints = re.split(r"\s*\|\|?\s*", constraints.strip())
    or_groups = []
    for constraints in or_constraints:
        and_constraints = re.split(
            r"(?<!^)(?<![=>< ,]) *(?<!-)[, ](?!-) *(?!,|$)", constraints
        )
        constraint_objects = []

        if len(and_constraints) > 1:
            for constraint in and_constraints:
                constraint_objects.append(parse_single_constraint(constraint))
        else:
            constraint_objects.append(parse_single_constraint(and_constraints[0]))

        constraint = constraint_objects[0]
        if len(constraint_objects) != 1:
            for next_constraint in constraint_objects[1:]:
                constraint = constraint.intersect(next_constraint)

        or_groups.append(constraint)

    return or_groups[0] if len(or_groups) == 1 else UnionConstraint(*or_groups)


def parse_single_constraint(constraint: str) -> Constraint:
    # Basic comparator
    m = BASIC_CONSTRAINT.match(constraint)
    if m:
        op = m.group(1)
        if op is None:
            op = "=="

        version = m.group(2).strip()

        return Constraint(version, op)

    raise ValueError(f"Could not parse version constraint: {constraint}")


__all__ = [
    "AnyConstraint",
    "BaseConstraint",
    "Constraint",
    "EmptyConstraint",
    "MultiConstraint",
    "UnionConstraint",
    "parse_constraint",
    "parse_single_constraint",
]
