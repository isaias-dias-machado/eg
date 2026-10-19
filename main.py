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
    | _newlines msg

_eve_list : eve_list_list
          | _eve_list "\n" eve_list_list

eve_list_list : "persist" -> evento
              | "send" ":=" "\"" "Send event %succession" "\"" -> evento
              | "recv" ":=" "\"" "Recv event" "\"" -> evento

msg : MESSAGES "{" "}"
    | MESSAGES "{" _newlines _msg_list _newlines "}" _newlines hist
    | _newlines hist
    

_msg_list : msg_list_list
          | _msg_list "\n" msg_list_list

msg_list_list : IDENTIFIER ":=" STRING
 
hist : HISTORY "{" "}"
     | HISTORY "{" _newlines _hist_list _newlines "}"

_hist_list : hist_block
           | _hist_list "\n\n" hist_block

hist_block : IDENTIFIER ":=" SEND IN IDENTIFIER TO ident_list "\n" _recv_list

_recv_list : RECV IN IDENTIFIER
           | _recv_list "\n" RECV IN IDENTIFIER

ident_list : IDENTIFIER
           | ident_list "," IDENTIFIER

_newlines: _NL _newlines
         |                      
                                
_NL: /\r?\n/                  

EVENTS: "Events"
PROCESSES: "Processes"
MESSAGES: "Messages"
HISTORY: "History"
IDENTIFIER: /[a-z][a-zA-Z0-9_]*/
STRING: /"[^"\n]*"/
SEND: "Send(" IDENTIFIER ")"
RECV: "Recv(" IDENTIFIER ")"
IN: "::"
TO: "->"

%ignore /[ \t]+/
"""

ex = """
Processes {
  p
  q
  r
}

Messages {
  request := "Request o que quiser"
  ack := "Ack"
  vote := "Votes for leader"
}

History {
  m1 := Send(request) :: p -> q
  Recv(m1) :: q

  m2 := Send(ack) :: q -> p, q, r
  Recv(m2) :: p                      
  Recv(m2) :: q

  m3 := Send(request) :: r -> q
  Recv(m2) :: r
}
"""

parser = Lark(grammar)
print(parser.parse(ex).pretty())
