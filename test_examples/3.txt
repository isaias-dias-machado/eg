Processes {
  p
  q
  r
}

Messages {
  request := "hello"
  ack := "ack"
}

History {
  m1 := Send(request) :: q -> p
  m2 := Send(ack) :: q -> p, q, r
  Recv(m2) :: q
}
