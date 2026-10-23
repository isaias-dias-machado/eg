Processes {
  p
}

Messages {
  request := "x"
}

History {
  m1 := Send(request) :: p -> q
}
