from functools import cache
from pathlib import Path

from lark import Lark, Tree
from lark.exceptions import UnexpectedInput

from .errors import ParseError

GRAMMAR_PATH = Path(__file__).with_name("grammar.lark")


@cache
def _get_parser() -> Lark:
    return Lark(
        GRAMMAR_PATH.read_text(),
        parser="earley",
        propagate_positions=True,
    )


def parse(source: str, *, source_name: str = "<string>") -> Tree:
    try:
        return _get_parser().parse(source)
    except UnexpectedInput as exc:
        raise ParseError.from_lark(exc, source, source_name) from exc
