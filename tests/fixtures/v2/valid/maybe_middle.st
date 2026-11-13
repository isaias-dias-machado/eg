Processes {
  p
  q
}

Messages {
  request := "Request"
  ack := "Ack"
}

History {
  m1 := Send(request) :: p -> q
  Maybe {
    m2 := Send(ack) :: q -> p
    Recv(m2) :: p
  }
  Recv(m1) :: q
}
