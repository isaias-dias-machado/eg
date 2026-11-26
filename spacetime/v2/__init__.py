"""The Space-Time DSL v2: adds ``Maybe`` blocks to ``History``.

The front end compiles a program up to the refined AST with a
tree-shaped history (see :mod:`spacetime.v2.ast`). The public surface is
re-exported by :mod:`spacetime`; typical use is :func:`compile_source`
or :func:`compile_file`.
"""

from ..errors import DslError, ParseError, SemanticError
from .ast import (
    Ast,
    History,
    HistoryItem,
    HistoryRefined,
    Ident,
    MaybeBlock,
    MaybeBlockRefined,
    MessageDeclaration,
    RecvEvent,
    RecvEventRefined,
    RefinedAst,
    RefinedHistoryItem,
    SendEvent,
    SendEventRefined,
    SourceLocation,
)
from .builder import AstBuilder, build_ast
from .compiler import StageObserver, compile_file, compile_source, parse
from .resolve import create_refined_ast

__all__ = [
    "Ast",
    "AstBuilder",
    "DslError",
    "History",
    "HistoryItem",
    "HistoryRefined",
    "Ident",
    "MaybeBlock",
    "MaybeBlockRefined",
    "MessageDeclaration",
    "ParseError",
    "RecvEvent",
    "RecvEventRefined",
    "RefinedAst",
    "RefinedHistoryItem",
    "SemanticError",
    "SendEvent",
    "SendEventRefined",
    "SourceLocation",
    "StageObserver",
    "build_ast",
    "compile_file",
    "compile_source",
    "create_refined_ast",
    "parse",
]
