Processes {
  p
  q
}

Messages {
  request := "Request"
}

History {
  Maybe {
    m1 := Send(request) :: p -> q
    Recv(m1) :: q
  }
  m2 := Send(request) :: q -> p
  Recv(m2) :: p
}
