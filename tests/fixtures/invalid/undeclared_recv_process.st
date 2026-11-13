Processes {
  p
  q
}

Messages {
  request := "x"
}

History {
  m1 := Send(request) :: p -> q
  Recv(m1) :: r // r is not declared (returns "undeclared process" instead of "not a recipient")
}

// undeclared_recv_process.st:12:15: error: undeclared process: 'r'
