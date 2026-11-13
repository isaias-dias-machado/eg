// Valid in v2: r is not a recipient of m1, so this Recv just means the message was not received there
Processes {
  p
  q
  r
}

Messages {
  request := "Request"
}

History {
  m1 := Send(request) :: p -> q
  Maybe {
    Recv(m1) :: r
  }
}
