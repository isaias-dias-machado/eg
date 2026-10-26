Processes { cliente servidor }
Messages { pedido := "Consultar informacao" }
History {
  var ativo : bool := true;
  if ativo {
    envio := Send(pedido) :: cliente -> servidor
  }
  Recv(envio) :: servidor
}
