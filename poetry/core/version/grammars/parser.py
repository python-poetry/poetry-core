from pathlib import Path

from lark import Lark


GRAMMAR_DIR = Path(__file__).parent

# Parser: PEP 440
# we use earley because the grammar is ambiguous
PARSER_PEP_440 = Lark.open(GRAMMAR_DIR / "pep440.lark", parser="earley", debug=False)

# Parser: PEP 508 Constraints
PARSER_PEP_508_CONSTRAINTS = Lark.open(
    GRAMMAR_DIR / "pep508.lark", parser="lalr", debug=False
)

# Parser: PEP 508 Environment Markers
PARSER_PEP_508_MARKERS = Lark.open(
    GRAMMAR_DIR / "markers.lark", parser="lalr", debug=False
)
