from dataclasses import dataclass

from lark import Tree
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
    declarations: list[Ident]
    location: SourceLocation


@dataclass(frozen=True)
class MessagesBlock:
    declarations: list[MessageDeclaration]
    location: SourceLocation


@dataclass(frozen=True)
class HistoryBlock:
    events: list[SendEvent | RecvEvent]
    location: SourceLocation


Block = ProcessesBlock | MessagesBlock | HistoryBlock


def _location_from_tree(tree: Tree) -> SourceLocation:
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


def _ident_from_token(token) -> Ident:
    return Ident(
        name=token.value,
        location=SourceLocation(token.line, token.column),
    )


class AstBuilder(Interpreter):
    def start(self, tree: Tree) -> Ast:
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
        events = [self.visit(child) for child in tree.children]
        return HistoryBlock(events, _location_from_tree(tree))

    def process_declaration(self, tree: Tree) -> Ident:
        return _ident_from_token(tree.children[0])

    def message_decl(self, tree: Tree) -> MessageDeclaration:
        name_node, value_node = tree.children
        name = self.visit(name_node)
        value = self.visit(value_node)
        return MessageDeclaration(name=name, value=value)

    def message_name(self, tree: Tree) -> Ident:
        return _ident_from_token(tree.children[0])

    def message_value(self, tree: Tree) -> str:
        return tree.children[0].value[1:-1]

    def message_identifier(self, tree: Tree) -> Ident:
        return _ident_from_token(tree.children[0])

    def process_identifier(self, tree: Tree) -> Ident:
        return _ident_from_token(tree.children[0])

    def event_identifier(self, tree: Tree) -> Ident:
        return _ident_from_token(tree.children[0])

    def process_list(self, tree: Tree) -> list[Ident]:
        return [self.visit(child) for child in tree.children]

    def event(self, tree: Tree) -> SendEvent | RecvEvent:
        return self.visit(tree.children[0])

    def send_event(self, tree: Tree) -> SendEvent:
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
        send_event_ref, process_ids = self.visit_children(tree)
        return RecvEvent(send_event_ref=send_event_ref, process_ids=process_ids)


def build_ast(tree: Tree) -> Ast:
    return AstBuilder().visit(tree)
