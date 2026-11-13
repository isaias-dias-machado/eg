Processes {
  p
  q
}

Messages {
  request := "Request"
}

History {
  Maybe {
    Recv(m1) :: q
  }
  m1 := Send(request) :: p -> q
}
