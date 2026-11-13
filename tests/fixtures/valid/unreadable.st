History {
  p := Send(p) :: p -> q
  q := Send(q) :: q -> p, q, r
  Recv(p) :: q
}

Processes {
  p
  q
  r
}

Messages {
  p := "hello"
  q := "ack"
}

