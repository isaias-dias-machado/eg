from lark import Lark, UnexpectedInput
import pathlib

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
