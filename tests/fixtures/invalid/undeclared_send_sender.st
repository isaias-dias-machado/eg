Processes {
  q
}

Messages {
  request := "x"
}

History {
  m1 := Send(request) :: p -> q
}

// undeclared_send_sender.st:10:26: error: undeclared process: 'p'
