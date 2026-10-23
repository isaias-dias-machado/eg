Processes {
  p
  q
  r
}

Messages {
  request := "x"
}

History {
  m1 := Send(request) :: p -> q
  Recv(m1) :: r
}
