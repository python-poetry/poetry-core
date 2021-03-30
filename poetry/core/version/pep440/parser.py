from typing import TYPE_CHECKING
from typing import List
from typing import Optional
from typing import Type

from lark import LarkError
from lark import Transformer

from poetry.core.version.exceptions import InvalidVersion
from poetry.core.version.grammars import GRAMMAR_PEP_440
from poetry.core.version.parser import Parser
from poetry.core.version.pep440 import Release
from poetry.core.version.pep440 import ReleaseTag


if TYPE_CHECKING:
    from poetry.core.version.pep440.version import PEP440Version

# Parser: PEP 440
# we use earley because the grammar is ambiguous
PARSER_PEP_440 = Parser(GRAMMAR_PEP_440, "earley", False)


class _Transformer(Transformer):
    def NUMERIC_IDENTIFIER(self, data: "Token"):  # noqa
        return int(data.value)

    def LOCAL_IDENTIFIER(self, data: "Token"):  # noqa
        try:
            return int(data.value)
        except ValueError:
            return data.value

    def POST_RELEASE_TAG(self, data: "Token"):  # noqa
        return data.value

    def PRE_RELEASE_TAG(self, data: "Token"):  # noqa
        return data.value

    def DEV_RELEASE_TAG(self, data: "Token"):  # noqa
        return data.value

    def LOCAL(self, data: "Token"):  # noqa
        return data.value

    def INT(self, data: "Token"):  # noqa
        return int(data.value)

    def version(self, children: List["Tree"]):  # noqa
        epoch, release, dev, pre, post, local = 0, None, None, None, None, None

        for child in children:
            if child.data == "epoch":
                # epoch is always a single numeric value
                epoch = child.children[0]
            elif child.data == "release":
                # release segment is of the form N(.N)*
                release = Release.from_parts(*child.children)
            elif child.data == "pre_release":
                # pre-release tag is of the form (a|b|rc)N
                pre = ReleaseTag(*child.children)
            elif child.data == "post_release":
                # post-release tags are of the form N (shortened) or post(N)*
                if len(child.children) == 1 and isinstance(child.children[0], int):
                    post = ReleaseTag("post", child.children[0])
                else:
                    post = ReleaseTag(*child.children)
            elif child.data == "dev_release":
                # dev-release tag is of the form dev(N)*
                dev = ReleaseTag(*child.children)
            elif child.data == "local":
                local = tuple(child.children)

        return epoch, release, pre, post, dev, local

    def start(self, children: List["Tree"]):  # noqa
        return children[0]


_TRANSFORMER = _Transformer()


def parse_pep440(
    value: str, version_class: Optional[Type["PEP440Version"]] = None
) -> "PEP440Version":
    if version_class is None:
        from poetry.core.version.pep440.version import PEP440Version

        version_class = PEP440Version

    try:
        tree = PARSER_PEP_440.parse(text=value)
        return version_class(*_TRANSFORMER.transform(tree), text=value)
    except (TypeError, LarkError):
        raise InvalidVersion(f"Invalid PEP 440 version: '{value}'")
