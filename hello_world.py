"""A tiny hello world for the `Interpreter` pattern used in main.py.

Two ideas to watch for:

* synthesis   -- each visit method *returns* a value, and the parent combines
                 the values returned by its children (bottom-up).
* inheritance -- `LoudHello` subclasses `Hello`, reuses the whole walk, and
                 replaces only `send_event` (top-down dispatch picks the most
                 specific method).

Run with:  .venv/bin/python hello_world.py
"""

import pathlib

from lark import Lark
from lark.visitors import Interpreter

GRAMMAR = pathlib.Path("grammar.lark").read_text()

PROGRAM = """
Processes {
  alice
  bob
}

Messages {
  hello := "hello world"
}

History {
  m1 := Send(hello) :: alice -> bob
  Recv(m1) :: bob
}
"""


class Hello(Interpreter):
    """Synthesize one greeting per Send event.

    State: `messages` maps a declared message name to its text.
    Precondition: Messages must appear before History (source order).
    Failure: KeyError if a Send refers to an undeclared message.
    """

    def __init__(self, greeting="hello"):
        super().__init__()
        self.greeting = greeting   # inherited context, available to subclasses
        self.messages = {}

    # Message declaration: hello := "hello world"
    def message_decl(self, tree):
        name, text = tree.children
        self.messages[name.children[0].value] = text.value.strip('"')

    # Send event: m1 := Send(hello) :: alice -> bob
    def send_event(self, tree):
        _, message, sender, recipients = tree.children
        text = self.messages[message.children[0].value]
        who = ", ".join(p.children[0].value for p in recipients.children)
        return f"{self.greeting}, {who}! {sender.children[0].value} says: {text}"

    # Receive events produce no greeting.
    def recv_event(self, tree):
        return None

    # event: send_event | recv_event -- pass the child's value up unchanged.
    def event(self, tree):
        (only_child,) = tree.children
        return self.visit(only_child)

    # Keep only the greetings (drop the None results from Recv).
    def history_block(self, tree):
        greetings = (self.visit(event) for event in tree.children)
        return [greeting for greeting in greetings if greeting is not None]

    # The root visits every block in source order, then returns the
    # greetings synthesized by the history block.
    def start(self, tree):
        greetings = []
        for block in tree.children:
            result = self.visit(block)
            if block.data == "history_block":
                greetings = result
        return greetings


class LoudHello(Hello):
    """Inheritance demo: same walk, louder synthesized text."""

    def __init__(self):
        super().__init__(greeting="HELLO")

    def send_event(self, tree):
        return super().send_event(tree).upper() + "!!!"


def main():
    tree = Lark(GRAMMAR).parse(PROGRAM)

    print("Hello says:")
    for line in Hello().visit(tree):
        print(" ", line)

    print("LoudHello says:")
    for line in LoudHello().visit(tree):
        print(" ", line)


if __name__ == "__main__":
    main()
