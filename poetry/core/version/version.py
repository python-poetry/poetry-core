import re

from collections import namedtuple
from itertools import dropwhile
from typing import Any
from typing import Optional
from typing import Tuple
from typing import Union

from .base import BaseVersion
from .exceptions import InvalidVersion
from .utils import Infinity
from .utils import NegativeInfinity


_Version = namedtuple("_Version", ["epoch", "release", "dev", "pre", "post", "local"])


VERSION_PATTERN = re.compile(
    r"""
    ^
    v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_.]?
            (?P<pre_l>(a|b|c|rc|alpha|beta|pre|preview))
            [-_.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_.]?
                (?P<post_l>post|rev|r)
                [-_.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_.]?
            (?P<dev_l>dev)
            [-_.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_.][a-z0-9]+)*))?       # local version
    $
""",
    re.IGNORECASE | re.VERBOSE,
)


class Version(BaseVersion):
    def __init__(self, version):  # type: (str) -> None
        # Validate the version and parse it into pieces
        match = VERSION_PATTERN.match(version)
        if not match:
            raise InvalidVersion("Invalid version: '{0}'".format(version))

        # Store the parsed out pieces of the version
        self._version = _Version(
            epoch=int(match.group("epoch")) if match.group("epoch") else 0,
            release=tuple(int(i) for i in match.group("release").split(".")),
            pre=_parse_letter_version(match.group("pre_l"), match.group("pre_n")),
            post=_parse_letter_version(
                match.group("post_l"), match.group("post_n1") or match.group("post_n2")
            ),
            dev=_parse_letter_version(match.group("dev_l"), match.group("dev_n")),
            local=_parse_local_version(match.group("local")),
        )

        # Generate a key which will be used for sorting
        self._key = _cmpkey(
            self._version.epoch,
            self._version.release,
            self._version.pre,
            self._version.post,
            self._version.dev,
            self._version.local,
        )

    def __repr__(self):  # type: () -> str
        return "<Version({0})>".format(repr(str(self)))

    def __str__(self):  # type: () -> str
        parts = []

        # Epoch
        if self._version.epoch != 0:
            parts.append("{0}!".format(self._version.epoch))

        # Release segment
        parts.append(".".join(str(x) for x in self._version.release))

        # Pre-release
        if self._version.pre is not None:
            parts.append("".join(str(x) for x in self._version.pre))

        # Post-release
        if self._version.post is not None:
            parts.append(".post{0}".format(self._version.post[1]))

        # Development release
        if self._version.dev is not None:
            parts.append(".dev{0}".format(self._version.dev[1]))

        # Local version segment
        if self._version.local is not None:
            parts.append("+{0}".format(".".join(str(x) for x in self._version.local)))

        return "".join(parts)

    @property
    def public(self):  # type: () -> str
        return str(self).split("+", 1)[0]

    @property
    def base_version(self):  # type: () -> str
        parts = []

        # Epoch
        if self._version.epoch != 0:
            parts.append("{0}!".format(self._version.epoch))

        # Release segment
        parts.append(".".join(str(x) for x in self._version.release))

        return "".join(parts)

    @property
    def local(self):  # type: () -> str
        version_string = str(self)
        if "+" in version_string:
            return version_string.split("+", 1)[1]

    @property
    def is_prerelease(self):  # type: () -> bool
        return bool(self._version.dev or self._version.pre)

    @property
    def is_postrelease(self):  # type: () -> bool
        return bool(self._version.post)


def _parse_letter_version(
    letter, number
):  # type: (str, Optional[str]) -> Tuple[str, int]
    if letter:
        # We consider there to be an implicit 0 in a pre-release if there is
        # not a numeral associated with it.
        if number is None:
            number = 0

        # We normalize any letters to their lower case form
        letter = letter.lower()

        # We consider some words to be alternate spellings of other words and
        # in those cases we want to normalize the spellings to our preferred
        # spelling.
        if letter == "alpha":
            letter = "a"
        elif letter == "beta":
            letter = "b"
        elif letter in ["c", "pre", "preview"]:
            letter = "rc"
        elif letter in ["rev", "r"]:
            letter = "post"

        return letter, int(number)
    if not letter and number:
        # We assume if we are given a number, but we are not given a letter
        # then this is using the implicit post release syntax (e.g. 1.0-1)
        letter = "post"

        return letter, int(number)


_local_version_seperators = re.compile(r"[._-]")


def _parse_local_version(local):  # type: (Optional[str]) -> Tuple[Union[str, int], ...]
    """
    Takes a string like abc.1.twelve and turns it into ("abc", 1, "twelve").
    """
    if local is not None:
        return tuple(
            part.lower() if not part.isdigit() else int(part)
            for part in _local_version_seperators.split(local)
        )


def _cmpkey(
    epoch,  # type: int
    release,  # type: Optional[Tuple[int, ...]]
    pre,  # type: Optional[Tuple[str, int]]
    post,  # type: Optional[Tuple[str, int]]
    dev,  # type: Optional[Tuple[str, int]]
    local,  # type: Optional[Tuple[Union[str, int], ...]]
):  # type: (...) -> Tuple[int, Tuple[int, ...], Union[Union[Infinity, NegativeInfinity, Tuple[str, int]], Any], Union[NegativeInfinity, Tuple[str, int]], Union[Union[Infinity, Tuple[str, int]], Any], Union[NegativeInfinity, Tuple[Union[Tuple[int, str], Tuple[NegativeInfinity, Union[str, int]]], ...]]]
    # When we compare a release version, we want to compare it with all of the
    # trailing zeros removed. So we'll use a reverse the list, drop all the now
    # leading zeros until we come to something non zero, then take the rest
    # re-reverse it back into the correct order and make it a tuple and use
    # that for our sorting key.
    release = tuple(reversed(list(dropwhile(lambda x: x == 0, reversed(release)))))

    # We need to "trick" the sorting algorithm to put 1.0.dev0 before 1.0a0.
    # We'll do this by abusing the pre segment, but we _only_ want to do this
    # if there is not a pre or a post segment. If we have one of those then
    # the normal sorting rules will handle this case correctly.
    if pre is None and post is None and dev is not None:
        pre = -Infinity

    # Versions without a pre-release (except as noted above) should sort after
    # those with one.
    elif pre is None:
        pre = Infinity

    # Versions without a post segment should sort before those with one.
    if post is None:
        post = -Infinity

    # Versions without a development segment should sort after those with one.
    if dev is None:
        dev = Infinity

    if local is None:
        # Versions without a local segment should sort before those with one.
        local = -Infinity
    else:
        # Versions with a local segment need that segment parsed to implement
        # the sorting rules in PEP440.
        # - Alpha numeric segments sort before numeric segments
        # - Alpha numeric segments sort lexicographically
        # - Numeric segments sort numerically
        # - Shorter versions sort before longer versions when the prefixes
        #   match exactly
        local = tuple((i, "") if isinstance(i, int) else (-Infinity, i) for i in local)

    return epoch, release, pre, post, dev, local
