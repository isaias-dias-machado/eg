"""Lark parse tree to ``Ast`` translation (stage 2 of the pipeline).

:class:`AstBuilder` is a Lark ``Interpreter`` whose method names match the
rules in ``grammar.lark``. It drops purely syntactic nodes, attaches source
locations to identifiers, and enforces structural rules that the grammar
cannot express: no repeated block and no duplicate declaration inside a
block.

Failure modes:
    Structural violations raise :class:`spacetime.errors.SemanticError` with
    the location of the offending block or declaration. An unexpected tree
    shape raises :class:`TypeError`, signalling that the grammar and this
    builder have drifted apart.
"""

from dataclasses import dataclass

from lark import Token, Tree
from lark.visitors import Interpreter

from .ast import (
    Ast,
    History,
    Ident,
    MessageDeclaration,
    RecvEvent,
    SendEvent,
    SourceLocation,
)
from .errors import SemanticError


@dataclass(frozen=True)
class ProcessesBlock:
    """Intermediate result for one ``Processes`` block.

    ``location`` is the block's own position and is used only to report a
    repeated block. ``declarations`` preserves source order.
    """

    declarations: list[Ident]
    location: SourceLocation


@dataclass(frozen=True)
class MessagesBlock:
    """Intermediate result for one ``Messages`` block.

    ``location`` is the block's own position and is used only to report a
    repeated block. ``declarations`` preserves source order.
    """

    declarations: list[MessageDeclaration]
    location: SourceLocation


@dataclass(frozen=True)
class HistoryBlock:
    """Intermediate result for one ``History`` block.

    ``location`` is the block's own position and is used only to report a
    repeated block. ``events`` preserves source order.
    """

    events: list[SendEvent | RecvEvent]
    location: SourceLocation


# Any block produced by ``AstBuilder`` before the blocks are merged into a
# single ``Ast``.
Block = ProcessesBlock | MessagesBlock | HistoryBlock


def _location_from_tree(tree: Tree) -> SourceLocation:
    """Return the best available source position for ``tree``.

    Lark attaches ``line``/``column`` to rule nodes because the parser runs
    with ``propagate_positions=True``. Some rules expose positions only on
    their children, so this falls back to the first positioned child and
    finally to ``SourceLocation(1, 1)``. The fallback keeps error reporting
    total instead of raising while another diagnostic is being produced.
    """
    line = getattr(tree.meta, "line", None)
    column = getattr(tree.meta, "column", None)
    if line is not None and column is not None:
        return SourceLocation(line, column)

    for child in tree.children:
        if isinstance(child, Tree) and child.children:
            child = child.children[0]

        line = getattr(child, "line", None)
        column = getattr(child, "column", None)
        if line is not None and column is not None:
            return SourceLocation(line, column)

    return SourceLocation(1, 1)


def _ident_from_token(token: Token) -> Ident:
    """Wrap a Lark identifier token as an ``Ident`` with its location.

    Invariants:
        ``token`` comes from one of the grammar's identifier rules, so it
        has ``value``, ``line`` and ``column``.
    """
    return Ident(
        name=token.value,
        location=SourceLocation(token.line, token.column),
    )


class AstBuilder(Interpreter):
    """Translate a parse tree into an :class:`Ast`.

    Methods are named after grammar rules and return the node for that
    rule. The visitor holds no state: create one instance per tree.

    Failure modes:
        See the module docstring: structural errors raise
        :class:`SemanticError` and unexpected shapes raise ``TypeError``.
    """

    def start(self, tree: Tree) -> Ast:
        """Merge the optional blocks into a single ``Ast``.

        Blocks may appear in any order. Missing blocks default to empty
        declarations and an empty history, so the empty source is valid.

        Failure modes:
            :class:`SemanticError` at the second occurrence of a block
            kind; ``TypeError`` for an unknown block type.
        """
        blocks: list[Block] = [self.visit(child) for child in tree.children]

        process_declarations: list[Ident] = []
        message_declarations: list[MessageDeclaration] = []
        history = History(events=[])
        seen_blocks: set[str] = set()

        for block in blocks:
            match block:
                case ProcessesBlock(declarations=declarations, location=location):
                    if "processes" in seen_blocks:
                        raise SemanticError(
                            "duplicate Processes block", location=location
                        )
                    seen_blocks.add("processes")
                    process_declarations = declarations
                case MessagesBlock(declarations=declarations, location=location):
                    if "messages" in seen_blocks:
                        raise SemanticError(
                            "duplicate Messages block", location=location
                        )
                    seen_blocks.add("messages")
                    message_declarations = declarations
                case HistoryBlock(events=events, location=location):
                    if "history" in seen_blocks:
                        raise SemanticError(
                            "duplicate History block", location=location
                        )
                    seen_blocks.add("history")
                    history = History(events=events)
                case _:
                    raise TypeError(f"unexpected block: {block!r}")

        return Ast(
            process_declarations=process_declarations,
            message_declarations=message_declarations,
            history=history,
        )

    def processes_block(self, tree: Tree) -> ProcessesBlock:
        """Collect process declarations, rejecting duplicate names.

        Invariants:
            The returned declarations are in source order and have unique
            names.

        Failure modes:
            :class:`SemanticError` at the second occurrence of a name.
        """
        declarations: list[Ident] = []
        seen: set[str] = set()

        for child in tree.children:
            declaration = self.visit(child)
            if declaration.name in seen:
                raise SemanticError(
                    f"duplicate process declaration: '{declaration.name}'",
                    location=declaration.location,
                )
            seen.add(declaration.name)
            declarations.append(declaration)

        return ProcessesBlock(declarations, _location_from_tree(tree))

    def messages_block(self, tree: Tree) -> MessagesBlock:
        """Collect message declarations, rejecting duplicate names.

        Invariants:
            The returned declarations are in source order and have unique
            names.

        Failure modes:
            :class:`SemanticError` at the second occurrence of a name.
        """
        declarations: list[MessageDeclaration] = []
        seen: set[str] = set()

        for child in tree.children:
            declaration = self.visit(child)
            name = declaration.name.name
            if name in seen:
                raise SemanticError(
                    f"duplicate message declaration: '{name}'",
                    location=declaration.name.location,
                )
            seen.add(name)
            declarations.append(declaration)

        return MessagesBlock(declarations, _location_from_tree(tree))

    def history_block(self, tree: Tree) -> HistoryBlock:
        """Collect history events in source order.

        No cross-event validation happens here: receives may still refer to
        unknown or later events until semantics runs.
        """
        events = [self.visit(child) for child in tree.children]
        return HistoryBlock(events, _location_from_tree(tree))

    def process_declaration(self, tree: Tree) -> Ident:
        """Return a declared process name with its location."""
        return _ident_from_token(tree.children[0])

    def message_decl(self, tree: Tree) -> MessageDeclaration:
        """Build a ``name := "value"`` declaration from its two children."""
        name_node, value_node = tree.children
        name = self.visit(name_node)
        value = self.visit(value_node)
        return MessageDeclaration(name=name, value=value)

    def message_name(self, tree: Tree) -> Ident:
        """Return the name identifier on the left of a message declaration."""
        return _ident_from_token(tree.children[0])

    def message_value(self, tree: Tree) -> str:
        """Return the payload with the outer double quotes stripped.

        No escape processing is performed; see
        :class:`spacetime.ast.MessageDeclaration`.
        """
        return tree.children[0].value[1:-1]

    def message_identifier(self, tree: Tree) -> Ident:
        """Return the message reference inside ``Send(...)``."""
        return _ident_from_token(tree.children[0])

    def process_identifier(self, tree: Tree) -> Ident:
        """Return a process used as sender, recipient, or receive target."""
        return _ident_from_token(tree.children[0])

    def event_identifier(self, tree: Tree) -> Ident:
        """Return an event name bound by a send or referenced by ``Recv``."""
        return _ident_from_token(tree.children[0])

    def process_list(self, tree: Tree) -> list[Ident]:
        """Return the comma-separated process identifiers in source order."""
        return [self.visit(child) for child in tree.children]

    def event(self, tree: Tree) -> SendEvent | RecvEvent:
        """Unwrap a history event into its send or receive form."""
        return self.visit(tree.children[0])

    def send_event(self, tree: Tree) -> SendEvent:
        """Build a send event from name, message, sender, and recipients."""
        name, message_id, process_from_id, processes_to_ids = self.visit_children(
            tree
        )
        return SendEvent(
            name=name,
            message_id=message_id,
            process_from_id=process_from_id,
            processes_to_ids=processes_to_ids,
        )

    def recv_event(self, tree: Tree) -> RecvEvent:
        """Build a receive event from the referenced send name and targets."""
        send_event_ref, process_ids = self.visit_children(tree)
        return RecvEvent(send_event_ref=send_event_ref, process_ids=process_ids)


def build_ast(tree: Tree) -> Ast:
    """Translate ``tree`` (the ``start`` rule) into an ``Ast``.

    Failure modes:
        Same as :class:`AstBuilder`.
    """
    return AstBuilder().visit(tree)
