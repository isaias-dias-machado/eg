Processes {
  p
  q
  r
}

Messages {
  request := "Request o que quiser"
  ack := "Ack"
  vote := "Votes for leader"
}

History {
  m1 := Send(request) :: p -> q
  Recv(m1) :: q

  m2 := Send(ack) :: q -> p, q, r
  Recv(m2) :: p, q

  m3 := Send(request) :: r -> q
  Recv(m3) :: q
}
