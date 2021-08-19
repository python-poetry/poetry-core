import re

from typing import Callable, Union

from .any_constraint import AnyConstraint
from .base_constraint import BaseConstraint
from .constraint import Constraint
from .empty_constraint import EmptyConstraint
from .multi_constraint import MultiConstraint
from .union_constraint import UnionConstraint


BASIC_CONSTRAINT = re.compile(r"^(!?==?)?\s*([^\s]+?)\s*$")
ConstraintTypes = Union[
    AnyConstraint, Constraint, UnionConstraint, EmptyConstraint, MultiConstraint
]

IN_CONSTRAINT = re.compile(r'in "([^"]+)"')
def parse_in_constraints(constraints: str, constraint_builder: Callable[[str], Constraint]) -> list[str]:
    m = IN_CONSTRAINT.match(constraints)
    if m:
        in_values = m.group(1).strip().split()
        return [constraint_builder(c.strip()) for c in in_values]

    raise ValueError(f"Cannot parse in constraint {constraints}")


def build_in_constraint(constraints: str) -> BaseConstraint:
    return UnionConstraint(*parse_in_constraints(constraints, lambda c: Constraint(c)))


def build_not_in_constraint(constraints: str) -> BaseConstraint:
    return MultiConstraint(*parse_in_constraints(constraints, lambda c: Constraint(c, operator = "!=")))


def parse_constraint(
    constraints: str,
) -> Union[AnyConstraint, UnionConstraint, Constraint]:
    if constraints == "*":
        return AnyConstraint()

    if constraints.startswith("in "):
        return build_in_constraint(constraints)
    if constraints.startswith("not in "):
        return build_not_in_constraint(constraints[4::])

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
        return UnionConstraint(*or_groups)


def parse_single_constraint(constraint: str) -> Constraint:
    # Basic comparator
    m = BASIC_CONSTRAINT.match(constraint)
    if m:
        op = m.group(1)
        if op is None:
            op = "=="

        version = m.group(2).strip()

        return Constraint(version, op)

    raise ValueError("Could not parse version constraint: {}".format(constraint))
