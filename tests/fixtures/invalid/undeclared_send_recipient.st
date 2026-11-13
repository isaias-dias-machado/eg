Processes {
  p
}

Messages {
  request := "x"
}

History {
  m1 := Send(request) :: p -> q // q is not received
}

// undeclared_send_recipient.st:10:31: error: undeclared process: 'q'
