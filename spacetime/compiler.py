"""Public compiler pipeline: parse, build, and refine.

The three stages are exposed separately for tests, but callers should use
:func:`compile_source` or :func:`compile_file` to get a consistent
``RefinedAst``.
"""

from pathlib import Path

from .ast import RefinedAst
from .builder import build_ast
from .errors import DslError
from .parser import parse
from .semantics import create_refined_ast


def compile_source(source: str, *, source_name: str = "<string>") -> RefinedAst:
    """Compile DSL text into a refined AST.

    ``source_name`` labels diagnostics. It is attached to any ``DslError``
    that does not already carry one, so errors raised by later stages point
    at the file rather than at a bare line number.

    Failure modes:
        Raises :class:`spacetime.errors.ParseError` or
        :class:`spacetime.errors.SemanticError` for invalid input. The
        original exception instance is re-raised (mutated only to fill in
        ``source_name``), so callers keep its location.
    """
    try:
        tree = parse(source, source_name=source_name)
        ast = build_ast(tree)
        return create_refined_ast(ast)
    except DslError as exc:
        if exc.source_name is None:
            exc.source_name = source_name
        raise


def compile_file(path: str | Path) -> RefinedAst:
    """Read ``path`` and compile it, using the path as ``source_name``.

    Failure modes:
        Propagates ``OSError`` from reading the file. Syntax and semantic
        errors behave as in :func:`compile_source`.
    """
    source_path = Path(path)
    return compile_source(
        source_path.read_text(),
        source_name=str(source_path),
    )
