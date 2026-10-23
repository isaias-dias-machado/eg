
Messages {
  request := "hello"
  ack := "ack"
} Processes {
  p
  q
  r
} History {
  m1 := Send(request) :: q -> p
  m2 := Send(ack) :: q -> p, q, r
  Recv(m2) :: q
}
