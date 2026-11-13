Processes {
  p
  q
}

Messages {
  request := "x"
}

History {
  Recv(m1) :: q // use of undeclared variable
  m1 := Send(request) :: p -> q
}

// later_event.st:11:8: error: undeclared send event: 'm1'
