from lark import Lark, Transformer

grammar = r"""
start : _newlines proc _newlines

proc : PROCESSES "{" "}"
        | PROCESSES "{" _newlines _proc_list _newlines "}"
        | PROCESSES "{" _newlines _proc_list _newlines "}" _newlines eve

_proc_list : IDENTIFIER
          | _proc_list "\n" IDENTIFIER

eve : EVENTS "{" "}"
    | EVENTS "{" _newlines _eve_list _newlines "}"
    | EVENTS "{" _newlines _eve_list _newlines "}" _newlines msg

_eve_list : eve_list_list
          | _eve_list "\n" eve_list_list

eve_list_list : "persist" -> evento
              | "send" ":=" "\"" "Send event %succession" "\"" -> evento
              | "recv" ":=" "\"" "Recv event" "\"" -> evento

msg : MESSAGES "{" "}"
    | MESSAGES "{" _newlines _msg_list _newlines "}"
    

_msg_list : msg_list_list
          | _msg_list "\n" msg_list_list

msg_list_list : "write" _r_arrow "\"" "Write" "\"" -> mensagem
              | "ack" _r_arrow "\"" "Ack" "\"" -> mensagem

_r_arrow : "::" "send" "->" "recv" "::"

hist : HISTORY "{" "}"
      | HISTORY "{" _newlines hist_list _newlines "}"

hist_list : hist_list_list
          | hist_list "\n" hist_list_list

hist_list_list : 

 

_newlines: _NL _newlines
         |                      // o OU/pipe vazio representa o mesmo que dizer _NL*:
                                // dá match a nenhuma ou várias newlines;
                                // e chama-se epsilon ou empty production

_NL: /\r?\n/                    // \r? para compatibilidade com DOS/Windows

EVENTS: "Events"
PROCESSES: "Processes"
MESSAGES: "Messages"
HISTORY: "History"
IDENTIFIER: /[a-z][a-zA-Z0-9_]*/

%ignore /[ \t]+/
"""

ex = """
Processes {
  processP
  processQ
  processR
}

Events {
  persist
  send := "Send event %succession"
  recv := "Recv event"
}

Messages {
  write :: send -> recv :: "Write"
  ack   :: send -> recv :: "Ack"
}

"""

parser = Lark(grammar)
print(parser.parse(ex).pretty())
