"""Public v2 compiler pipeline: parse, build, and resolve.

Same three stages as :mod:`spacetime.compiler`, driven by the shared
:func:`spacetime.compiler.run_pipeline` with the v2 grammar, builder and
resolver. Callers should use :func:`compile_source` or :func:`compile_file`
to get a consistent v2 ``RefinedAst``.
"""

from pathlib import Path

from lark import Tree

from ..compiler import StageObserver, run_pipeline
from ..parser import parse as _parse
from .ast import RefinedAst
from .builder import build_ast
from .resolve import create_refined_ast

GRAMMAR_PATH = Path(__file__).with_name("grammar.lark")


def parse(source: str, *, source_name: str = "<string>") -> Tree:
    """Parse v2 DSL ``source`` into a Lark tree using the v2 grammar.

    Failure modes:
        Same as :func:`spacetime.parser.parse`.
    """
    return _parse(source, source_name=source_name, grammar_path=GRAMMAR_PATH)


def compile_source(
    source: str,
    *,
    source_name: str = "<string>",
    observe: StageObserver | None = None,
) -> RefinedAst:
    """Compile v2 DSL text into a refined AST.

    Behaves as :func:`spacetime.compiler.compile_source`, but with the v2
    grammar and the tree-shaped history (``Maybe`` blocks).

    Failure modes:
        Same as :func:`spacetime.compiler.run_pipeline`.
    """
    return run_pipeline(
        source,
        source_name=source_name,
        observe=observe,
        grammar_path=GRAMMAR_PATH,
        build=build_ast,
        resolve=create_refined_ast,
    )


def compile_file(
    path: str | Path,
    *,
    observe: StageObserver | None = None,
) -> RefinedAst:
    """Read ``path`` and compile it with the v2 pipeline.

    ``observe`` behaves as in :func:`compile_source`.

    Failure modes:
        Propagates ``OSError`` from reading the file. Syntax and semantic
        errors behave as in :func:`compile_source`.
    """
    source_path = Path(path)
    return compile_source(
        source_path.read_text(),
        source_name=str(source_path),
        observe=observe,
    )
