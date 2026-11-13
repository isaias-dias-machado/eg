Processes {
  p
  q
}

History {
  m1 := Send(request) :: p -> q // `request` undeclared
}

// undeclared_message.st:7:14: error: undeclared message: 'request'
