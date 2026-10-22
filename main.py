from lark import Lark, UnexpectedInput
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

try:
    parser = Lark(grammar)
    print(parser.parse(ex).pretty())
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
