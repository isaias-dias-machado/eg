from typing import Set

from enum import Enum

from dataclasses import dataclass

from lark import Lark, UnexpectedInput
from lark.visitors import Interpreter
import pathlib
import os

import pprint

grammar = pathlib.Path('grammar.lark').read_text()

ex = """
Processes {
  p
  q
  r
}

Messages {
  request := "hello"
  ack := "ack"
}

History {
  m1 := Send(request) :: q -> p
  m2 := Send(ack) :: q -> p, q, r
  Recv(m2) :: q
}
"""

# class SemanticState:
#     def __init(self):
#         self.process_declarations = set()
#         self.message_declarations: dict[str, str] = dict()

@dataclass
class MessageDeclaration:
    identifier: str
    value: str

@dataclass
class SendEvent:
    temporal_pos: int
    name: str
    message_id: str
    process_from_id: str
    processes_to_ids: list[str]

@dataclass
class RecvEvent:
    temporal_pos: int
    send_event_ref: str
    process_ids: list[str]

@dataclass
class History:
    num_events: int
    events: list[SendEvent | RecvEvent]

@dataclass
class Ast:
    process_declarations: set[str]
    message_declarations: dict[str, str]
    history: History

def print_ast(ast: Ast):
    print(f"Ast")
    print("\tprocess_declarations")
    [print("\t\t", dec) for dec in ast.process_declarations]
    print("\tmessage_declarations")
    [print("\t\t", key, ":", value) for key, value in ast.message_declarations.items()]
    print("\thistory")
    print("\t\tevent_number", ast.history.num_events)
    for item in ast.history.events:
        print("\t\t", end="")
        pprint.pp(item)

class BranchKind(Enum):
    PROCESSES = 0
    MESSAGES = 1
    HISTORY = 2

class SemanticError(Exception):
    def __init__(self, message, node=None):
        self.node = node
        super().__init__(message)


# A first normaliztion pass is done to allow blocks to be declared in any order
# Validations performed here: repeated process and message declarations
class AstNormalizer(Interpreter):
    def __init__(self):
        self.temporal_pos_counter = 0
    def start(self, tree):
        branches = [(self.visit(child)) for child in tree.children]
        process_declarations = set()
        message_declarations = {}
        history = None
        for (branch, obj) in branches:
            match branch:
                case BranchKind.PROCESSES:
                    process_declarations = obj
                case BranchKind.MESSAGES:
                    message_declarations = obj
                case BranchKind.HISTORY:
                    history = obj

        if history is None:
            raise Exception("history uninitialized")

        return Ast(
                process_declarations,
                message_declarations,
                history
        )

    def processes_block(self, tree) -> tuple[BranchKind, set[str]]:
        set_of_proc_declarations = set()
        for child in tree.children:
            declaration = self.visit(child)
            if declaration in set_of_proc_declarations:
                raise SemanticError(f"duplicate process declaration: '{declaration}'")
            else:
                set_of_proc_declarations.add(declaration)

        return (BranchKind.PROCESSES, set_of_proc_declarations)
        
    def history_block(self, tree):
        event_number = len(tree.children)
        event_list = [self.visit(child) for child in tree.children]
        return (BranchKind.HISTORY, History(event_number, event_list))

    def messages_block(self, tree) -> tuple[BranchKind, dict[str, str]]:
        declarations: dict[str, str] = {}
        for child in tree.children:
            key, value = self.visit(child)
            if key in declarations:
                raise SemanticError(f"duplicate message declaration: '{key}'")
            declarations[key] = value
        return (BranchKind.MESSAGES, declarations)

    def process_declaration(self, tree) -> str:
        return tree.children[0].value

    def message_decl(self, tree) -> tuple[str, str]:
        name_node, value_node = tree.children
        name = self.visit(name_node)
        value = self.visit(value_node)
        return (name, value)

    def message_name(self, tree) -> str:
        return tree.children[0].value

    def message_value(self, tree) -> str:
        return tree.children[0].value.strip('"')

    def message_identifier(self, tree) ->str:
        return tree.children[0].value

    def process_identifier(self, tree) ->str:
        return tree.children[0].value

    def event_identifier(self, tree) -> str:
        return tree.children[0].value

    def process_list(self, tree) -> list[str]:
        return [self.visit(child) for child in tree.children]

    def event(self, tree) -> SendEvent | RecvEvent:
        return self.visit(tree.children[0])

    def send_event(self, tree) -> SendEvent:
        temporal_pos = self.temporal_pos_counter
        self.temporal_pos_counter += 1
        name, message_id, process_from_id, process_to_ids = self.visit_children(tree)
        return SendEvent(temporal_pos, name, message_id, process_from_id, process_to_ids)

    def recv_event(self, tree):
        temporal_pos = self.temporal_pos_counter
        self.temporal_pos_counter += 1
        send_event_ref, process_ids = self.visit_children(tree)
        return RecvEvent(temporal_pos, send_event_ref, process_ids)

@dataclass
class RecvEventRefined:
    temporal_pos: int
    related_send_event: SendEvent
    process_ids: list[str]

@dataclass
class SendEventRefined:
    temporal_pos: int
    message: str
    process_from_id: str
    processes_to_ids: list[str]

@dataclass
class HistoryRefined:
    num_events: int
    events: list[SendEvent | RecvEventRefined]

@dataclass
class RefinedAst:
    process_declarations: set[str]
    history: HistoryRefined


# TODO: create a DuplicatedReferenceError that extands SemanticError standardizes the message
def create_refined_ast(ast: Ast) -> RefinedAst:
    send_events: dict[str, SendEventRefined] = {}
    refined_events = []
    for event in ast.history.events:
        match event:
            case SendEvent(temporal_pos, name, message_id, process_from_id, processes_to_ids):
                if name in send_events:
                    raise SemanticError(f"duplicate event declaration: '{name}'")
                else:
                    refined_event = SendEventRefined(temporal_pos, ast.message_declarations[message_id], process_from_id, processes_to_ids)
                    send_events[name] = refined_event
                    refined_events.append(refined_event)
            case RecvEvent(temporal_pos, send_event_ref, process_ids):
                if send_event_ref not in send_events:
                    raise SemanticError(f"undeclared reference: '{send_event_ref}'")
                else:
                    refined_events.append(RecvEventRefined(temporal_pos, send_events[send_event_ref], process_ids))
        
    return RefinedAst(ast.process_declarations, HistoryRefined(ast.history.num_events, refined_events))

def print_refined_ast(ast: Ast):
    print(f"Ast")
    print("\tprocess_declarations")
    [print("\t\t", dec) for dec in ast.process_declarations]
    print("\thistory")
    print("\t\tevent_number", ast.history.num_events)
    for item in ast.history.events:
        print("\t\t", end="")
        pprint.pp(item)

try:
    parser = Lark(grammar)
    tree = parser.parse(ex)
    ast = AstNormalizer().visit(tree)
    # print(tree.pretty())
    # print_ast(ast)
    refined_ast = create_refined_ast(ast)
    print_refined_ast(refined_ast)
except UnexpectedInput as e:
    print(e)
    exit(1)

test_examples_dir = "./test_examples/"
for file in os.listdir(test_examples_dir):
    filepath = test_examples_dir + file
    print("Parsing file:", filepath, "...")
    contents = pathlib.Path(filepath).read_text()
    parser.parse(contents)
    print("Ok!")
