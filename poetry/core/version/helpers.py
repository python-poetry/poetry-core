from typing import TYPE_CHECKING
from typing import Union

from poetry.core.semver.helpers import parse_constraint
from poetry.core.semver.version import Version
from poetry.core.semver.version_union import VersionUnion


if TYPE_CHECKING:
    from poetry.core.semver.version_constraint import VersionConstraint  # noqa

PYTHON_VERSION = [
    "2.7.*",
    "3.0.*",
    "3.1.*",
    "3.2.*",
    "3.3.*",
    "3.4.*",
    "3.5.*",
    "3.6.*",
    "3.7.*",
    "3.8.*",
    "3.9.*",
    "3.10.*",
]


def format_python_constraint(
    constraint: Union[Version, VersionUnion, "VersionConstraint"],
) -> str:
    """
    This helper will help in transforming
    disjunctive constraint into proper constraint.
    """
    if isinstance(constraint, Version):
        if constraint.precision >= 3:
            return "=={}".format(str(constraint))

        # Transform 3.6 or 3
        if constraint.precision == 2:
            # 3.6
            constraint = parse_constraint(
                "~{}.{}".format(constraint.major, constraint.minor)
            )
        else:
            constraint = parse_constraint("^{}.0".format(constraint.major))

    if not isinstance(constraint, VersionUnion):
        return str(constraint)

    formatted = []
    accepted = []

    for version in PYTHON_VERSION:
        version_constraint = parse_constraint(version)
        matches = constraint.allows_any(version_constraint)
        if not matches:
            formatted.append("!=" + version)
        else:
            accepted.append(version)

    # Checking lower bound
    low = accepted[0]

    formatted.insert(0, ">=" + ".".join(low.split(".")[:2]))

    return ", ".join(formatted)
