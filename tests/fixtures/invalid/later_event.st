Processes {
  p
  q
}

Messages {
  request := "x"
}

History {
  Recv(m1) :: q
  m1 := Send(request) :: p -> q
}
