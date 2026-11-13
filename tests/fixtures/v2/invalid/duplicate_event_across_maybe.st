Processes {
  p
  q
}

Messages {
  request := "Request"
}

History {
  m1 := Send(request) :: p -> q
  Maybe {
    m1 := Send(request) :: q -> p
  }
  Recv(m1) :: q
}
