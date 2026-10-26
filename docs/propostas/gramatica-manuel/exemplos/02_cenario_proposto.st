Processes {
  cliente
  servidor
}

Messages {
  pedido := "Consultar informacao"
  resposta := "Informacao disponivel"
}

History {
  var limite : int := 2;
  var concluidas : int := 0;
  var responder : bool := true;

  repeat limite {
    envio := Send(pedido) :: cliente -> servidor
    Recv(envio) :: servidor

    if responder {
      retorno := Send(resposta) :: servidor -> cliente
      Recv(retorno) :: cliente
      concluidas := concluidas + 1;
    } else {
      responder := true;
    }
  }
}
