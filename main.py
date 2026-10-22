from typing import Set

from dataclasses import dataclass

from lark import Lark, UnexpectedInput
from lark.visitors import Interpreter
import pathlib
import os

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

class TreeInt(Interpreter):
    def __init__(self, log = None):
        super().__init__()
        self.scopes = [{}]
        self.depth = 0
        self.log = log or (lambda msg: None)    # pass print to enable tracing

    def visit(self, tree):
        self.log(f"{'  ' * self.depth}> {tree.data} @{getattr(tree.meta, 'line', '?')}")
        self.depth += 1
        before = len(self.scopes)
        try:
            result = super().visit(tree)
        finally:
            self.depth -= 1
            if len(self.scopes) != before:
                raise RuntimeError(f"scope leak in {tree.data}: push without pop")
        self.log(f"{'  ' * self.depth}< {tree.data} = {result!r}")
        return result
        
    def processes_block(self, tree):
        for d in tree.children:
            return d.children[0].value
    #
    # def messages_block(self, tree):
    #     node1, node2 = tree.children[0].children
    #     message_name = node1.children[0].value
    #     name_string = node2.value
    #     self.state.message_declarations[message_name] = name_string

try:
    parser = Lark(grammar)
    tree = parser.parse(ex)
    TreeInt(log=print).visit(tree)
    # print(process_declarations)
    # print(message_declarations)
    print(tree.pretty())
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
