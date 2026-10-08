from lark import Lark, Transformer

grammar = r"""
start : _newlines keyword _newlines

keyword : EVENTS "{"  "}"
        | PROCESSES "{" _newlines id_list _newlines "}"
        | MESSAGES  "{"  "}"
        | HISTORY 

id_list: IDENTIFIER
       | id_list "\n"

_newlines: _NL _newlines
         |                      // o OU/pipe vazio representa o mesmo que dizer _NL*:
                                // dá match a nenhuma ou várias newlines;
                                // e chama-se epsilon ou empty production

_NL: /\r?\n/                    // \r? para compatibilidade com DOS/Windows

EVENTS: "events"
PROCESSES: "Processes"
MESSAGES: "messages"
HISTORY: "history"
IDENTIFIER: /[a-z][a-zA-Z0-9_]*/

%ignore /[ \t]+/
"""

ex = """
Processes {
  processP
  processQ
  processR
}
"""

parser = Lark(grammar)
print(parser.parse(ex).pretty())
