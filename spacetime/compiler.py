from pathlib import Path

from .ast import RefinedAst
from .builder import build_ast
from .errors import DslError
from .parser import parse
from .semantics import create_refined_ast


def compile_source(source: str, *, source_name: str = "<string>") -> RefinedAst:
    try:
        tree = parse(source, source_name=source_name)
        ast = build_ast(tree)
        return create_refined_ast(ast)
    except DslError as exc:
        if exc.source_name is None:
            exc.source_name = source_name
        raise


def compile_file(path: str | Path) -> RefinedAst:
    source_path = Path(path)
    return compile_source(
        source_path.read_text(),
        source_name=str(source_path),
    )
