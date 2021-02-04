import urllib.parse as urlparse

from poetry.core.semver.exceptions import ParseConstraintError
from poetry.core.semver.helpers import parse_constraint

from .grammars.parser import Parser
from .markers import _compact_markers


class InvalidRequirement(ValueError):
    """
    An invalid requirement was found, users should refer to PEP 508.
    """


_parser = Parser("pep508")


class Requirement(object):
    """
    Parse a requirement.

    Parse a given requirement string into its parts, such as name, specifier,
    URL, and extras. Raises InvalidRequirement on a badly-formed requirement
    string.
    """

    def __init__(self, requirement_string: str) -> None:
        from lark import UnexpectedCharacters
        from lark import UnexpectedToken

        try:
            parsed = _parser.parse(requirement_string)
        except (UnexpectedCharacters, UnexpectedToken) as e:
            raise InvalidRequirement(
                "The requirement is invalid: Unexpected character at column {}\n\n{}".format(
                    e.column, e.get_context(requirement_string)
                )
            )

        self.name = next(parsed.scan_values(lambda t: t.type == "NAME")).value
        url = next(parsed.scan_values(lambda t: t.type == "URI"), None)

        if url:
            url = url.value
            parsed_url = urlparse.urlparse(url)
            if parsed_url.scheme == "file":
                if urlparse.urlunparse(parsed_url) != url:
                    raise InvalidRequirement(
                        'The requirement is invalid: invalid URL "{0}"'.format(url)
                    )
            elif (
                not (parsed_url.scheme and parsed_url.netloc)
                or (not parsed_url.scheme and not parsed_url.netloc)
            ) and not parsed_url.path:
                raise InvalidRequirement(
                    'The requirement is invalid: invalid URL "{0}"'.format(url)
                )
            self.url = url
        else:
            self.url = None

        self.extras = [e.value for e in parsed.scan_values(lambda t: t.type == "EXTRA")]
        constraint = next(parsed.find_data("version_specification"), None)
        if not constraint:
            constraint = "*"
        else:
            constraint = ",".join(constraint.children)

        try:
            self.constraint = parse_constraint(constraint)
        except ParseConstraintError:
            raise InvalidRequirement(
                'The requirement is invalid: invalid version constraint "{}"'.format(
                    constraint
                )
            )

        self.pretty_constraint = constraint

        marker = next(parsed.find_data("marker_spec"), None)
        if marker:
            marker = _compact_markers(
                marker.children[0].children, tree_prefix="markers__"
            )

        self.marker = marker

    def __str__(self) -> str:
        parts = [self.name]

        if self.extras:
            parts.append("[{0}]".format(",".join(sorted(self.extras))))

        if self.pretty_constraint:
            parts.append(self.pretty_constraint)

        if self.url:
            parts.append("@ {0}".format(self.url))

        if self.marker:
            parts.append("; {0}".format(self.marker))

        return "".join(parts)

    def __repr__(self) -> str:
        return "<Requirement({0!r})>".format(str(self))
