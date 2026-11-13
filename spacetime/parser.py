"""Lark front end: DSL text to parse tree (stage 1 of the pipeline).

The grammar lives next to this module, so parsing does not depend on the
process working directory. The parser is built once per process and shared.
"""

from functools import cache
from pathlib import Path

from lark import Lark, Tree
from lark.exceptions import UnexpectedInput

from .errors import ParseError

GRAMMAR_PATH = Path(__file__).with_name("grammar.lark")


@cache
def _get_parser(grammar_path: Path = GRAMMAR_PATH) -> Lark:
    """Return the shared Earley parser for ``grammar_path``, building it on first use.

    One parser is cached per grammar file, so the v1 grammar and the v2
    grammar (``spacetime/v2/grammar.lark``) coexist in the same process.

    Invariants:
        The grammar file does not change at runtime.
        ``propagate_positions`` is required so the builder can attach
        source locations to identifiers.

    Failure modes:
        Propagates ``OSError`` if the grammar file is missing or unreadable.
    """
    return Lark(
        Path(grammar_path).read_text(),
        parser="earley",
        propagate_positions=True,
    )


def parse(
    source: str,
    *,
    source_name: str = "<string>",
    grammar_path: Path = GRAMMAR_PATH,
) -> Tree:
    """Parse DSL ``source`` into a Lark tree.

    ``source_name`` is used only as the file label in error messages.
    ``grammar_path`` selects the language version; it defaults to the v1
    grammar next to this module.

    Failure modes:
        Raises :class:`spacetime.errors.ParseError` with a source excerpt
        for any ``UnexpectedInput`` reported by Lark. Other exceptions
        propagate unchanged.
    """
    try:
        return _get_parser(grammar_path).parse(source)
    except UnexpectedInput as exc:
        raise ParseError.from_lark(exc, source, source_name) from exc
