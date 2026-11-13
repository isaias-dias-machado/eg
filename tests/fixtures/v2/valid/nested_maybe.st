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
    Maybe {
      m3 := Send(request) :: p -> q
      Recv(m3) :: q
    }
    Recv(m2) :: p
  }
  Recv(m1) :: q
}
