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
