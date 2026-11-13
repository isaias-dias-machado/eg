Processes {
  p
  q
}

Messages {
  request := "x"
}

History {
  m1 := Send(request) :: p -> q
  m1 := Send(request) :: p -> q // duplicate variable declaration
}

// duplicate_event.st:12:3: error: duplicate event declaration: 'm1'
