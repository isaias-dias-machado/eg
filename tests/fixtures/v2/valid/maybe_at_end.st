Processes {
  p
  q
}

Messages {
  request := "Request"
}

History {
  m1 := Send(request) :: p -> q
  Recv(m1) :: q
  Maybe {
    m2 := Send(request) :: q -> p
    Recv(m2) :: p
  }
}
