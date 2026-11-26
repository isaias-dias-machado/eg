Processes {
  p
  q
  r
}

Messages {
  request := "Request o que quiser"
  ack := "Ack"
  vote := "Votes for leader"
}

History {
  m1 := Send(request) :: p -> q
  Recv(m1) :: q

  Maybe {
    m2 := Send(ack) :: q -> p, q, r
    Maybe {
      Recv(m2) :: p, q
    }
    Maybe {
      new := Send(request)
    }
  }

  m3 := Send(request) :: r -> q
  Recv(m3) :: q
}
