Processes {
  cliente
  servidor
}

Messages {
  pedido := "Consultar informacao"
}

History {
  envio := Send(pedido) :: cliente -> servidor
  Recv(envio) :: servidor
}
