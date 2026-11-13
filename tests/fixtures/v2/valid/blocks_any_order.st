History {
  m1 := Send(request) :: p -> q
  Maybe {
    Recv(m1) :: q
  }
}

Messages {
  request := "Request"
}

Processes {
  p
  q
}
