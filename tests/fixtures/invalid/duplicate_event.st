Processes {
  p
  q
}

Messages {
  request := "x"
}

History {
  m1 := Send(request) :: p -> q
  m1 := Send(request) :: p -> q
}
