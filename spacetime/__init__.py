"""Space-Time DSL: compile a message history into a refined AST.

The language is v2 (``Maybe`` blocks inside ``History``); the
implementation lives in :mod:`spacetime.v2` and its public surface is
re-exported here. Typical use is :func:`compile_source` or
:func:`compile_file`.
"""

from .v2 import (
    Ast,
    AstBuilder,
    DslError,
    History,
    HistoryItem,
    HistoryRefined,
    Ident,
    MaybeBlock,
    MaybeBlockRefined,
    MessageDeclaration,
    ParseError,
    RecvEvent,
    RecvEventRefined,
    RefinedAst,
    RefinedHistoryItem,
    SemanticError,
    SendEvent,
    SendEventRefined,
    SourceLocation,
    StageObserver,
    build_ast,
    compile_file,
    compile_source,
    create_refined_ast,
    parse,
)

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
