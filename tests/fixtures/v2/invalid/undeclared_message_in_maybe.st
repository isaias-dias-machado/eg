Processes {
  p
  q
}

Messages {
  request := "Request"
}

History {
  Maybe {
    m1 := Send(ack) :: p -> q
  }
}
