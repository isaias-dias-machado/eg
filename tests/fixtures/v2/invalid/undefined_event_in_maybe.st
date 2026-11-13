Processes {
  p
  q
}

Messages {
  request := "Request"
}

History {
  Maybe {
    Recv(m9) :: q
  }
}
