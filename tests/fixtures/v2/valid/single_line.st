Processes { p q } Messages { request := "Request" } History { m1 := Send(request) :: p -> q Maybe { Recv(m1) :: q } }
