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
  Recv(m1) :: r // not a valid recipient for m1 (only `q` can receive)
}

// recv_not_recipient.st:13:15: error: process 'r' is not a recipient of send event 'm1'
