## Estado da proposta

**Proposta de Manuel Pereira para discussão com Pedro e Isaías.**

Engenharia Gramatical · MEI · Universidade do Minho · 2026/2027  
Versão: 0.1 · Data: 26 de outubro de 2026

Este documento propõe uma extensão da linguagem Space-Time já existente no projeto. Não representa uma decisão aprovada pelo grupo nem uma funcionalidade já implementada. A pasta contém apenas documentação, uma especificação EBNF e exemplos; não substitui o README principal, `spacetime/grammar.lark`, os módulos Python ou os testes existentes.

A análise de continuidade assenta no ZIP fornecido com identificador de arquivo `e949fceae727bacac956a750d83722c4720c8837`. Não se pressupõe que essa fotografia corresponda ao estado atual do GitHub. Antes da integração, o grupo deve comparar esta proposta com a versão corrente.

## Objetivo

Preservar a ideia de descrever comunicações entre processos para futura representação em diagramas espaço-tempo, acrescentando as capacidades mínimas pedidas na Parte I: variáveis, expressões, âmbitos, construções aninhadas, decisões e repetição.

A linguagem proposta descreve **cenários parametrizados de comunicação**. `if`, variáveis e ciclos controlam a construção de um cenário global; não representam automaticamente memória privada, execução concorrente ou decisões autónomas de cada processo. Esse significado teria de ser especificado à parte caso o grupo pretendesse modelá-lo.

O nome Lamport é mantido como contexto da ideia original. A posição sequencial de um evento não é, por si só, um relógio lógico de Lamport, nem prova uma ordem física global entre computadores.

## Conteúdo e ordem de leitura

| Ficheiro | Função |
| --- | --- |
| [README.md](README.md) | Conceito, nomenclatura, regras e proposta de integração |
| [gramatica.ebnf](gramatica.ebnf) | Especificação sintática proposta |
| [exemplos/01_base_atual.st](exemplos/01_base_atual.st) | Exemplo com as construções atuais |
| [exemplos/02_cenario_proposto.st](exemplos/02_cenario_proposto.st) | Exemplo com variáveis, condição e ciclo |
| [exemplos/03_invalido_ambito.st](exemplos/03_invalido_ambito.st) | Exemplo a rejeitar por referência fora do âmbito |
| [exemplos/04_invalido_tipo.st](exemplos/04_invalido_tipo.st) | Exemplo a rejeitar por incompatibilidade de tipos |

Os exemplos 02–04 são casos de especificação da extensão, não testes executáveis do compilador atual. O exemplo 01 é o único destinado a execução no compilador atual. Não mover estes ficheiros para `tests/fixtures/valid` ou `tests/fixtures/invalid` antes de adaptar os testes: a suite atual inspeciona o conteúdo dessas pastas.

## Continuidade com o trabalho existente

| Elemento atual | Papel preservado | Evolução proposta |
| --- | --- | --- |
| `Processes` | Declara os participantes | Sem mudança da forma habitual |
| `Messages` | Associa nomes a conteúdos textuais | Mensagens continuam constantes |
| `History` | Contém o histórico | Passa a conter instruções estruturadas |
| `Send` | Descreve um envio | Pode ocorrer dentro de blocos e ciclos |
| `Recv` | Descreve uma receção | Referencia um envio disponível no contexto definido |
| `:=`, `::`, `->` | Definição, emissor/contexto e destino | Mantidos |
| `Ast` e `RefinedAst` | Representações internas | Precisariam de novos nós e regras, se aprovada a implementação |

A compatibilidade pretendida é conservar os exemplos usuais atuais. Não se afirma equivalência lexical integral: novas palavras reservadas podem colidir com identificadores antigos e ignorar quebras de linha altera o tratamento lexical. Estes pontos devem ser verificados antes de prometer compatibilidade total.

## Exemplo completo

```text
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
```

1. `cliente` e `servidor` são os participantes declarados.
2. `pedido` e `resposta` identificam conteúdos constantes.
3. `limite`, `concluidas` e `responder` são variáveis do cenário.
4. O valor de `limite` é avaliado na entrada do ciclo: o corpo executa duas vezes.
5. Em cada iteração há um envio de pedido e a respetiva receção.
6. `if responder` seleciona um ramo. Com o valor inicial `true`, executa-se o ramo de resposta em ambas as iterações.
7. Cada resposta recebida é seguida do incremento de `concluidas`.
8. O valor final de `concluidas` é 2. Esse valor é um resultado esperado da semântica proposta; o compilador atual não executa este programa.

## Notação da gramática

A especificação usa EBNF, uma forma compacta de escrever uma gramática independente de contexto. Não é um ficheiro Lark pronto a carregar. Para integração, é necessário traduzi-la para a notação Lark e definir as regras lexicais do analisador.

| Símbolo | Significado |
| --- | --- |
| `::=` | Define uma produção |
| `A \| B` | Alternativa |
| `[ A ]` | Elemento opcional |
| `{ A }` | Zero ou mais repetições na metalinguagem |
| `"{"` e `"}"` | Chavetas literais da linguagem |
| `IDENT`, `INT`, `STRING` | Categorias lexicais |
| Não terminal | Estrutura definida por outras produções |
| Terminal | Palavra ou símbolo efetivamente escrito no programa |

Exemplo: `ListaProcessos ::= IDENT { "," IDENT }` permite `cliente`, `cliente, servidor`, etc. Exige pelo menos um nome.

## Gramática proposta

A especificação integral está em [gramatica.ebnf](gramatica.ebnf). Os grupos principais são:

| Grupo | Produções | Responsabilidade |
| --- | --- | --- |
| Programa | `Programa`, `BlocoPrincipal` | Organização global |
| Declarações globais | `BlocoProcessos`, `BlocoMensagens` | Entidades do domínio |
| Estrutura local | `BlocoHistorico`, `Bloco`, `Instrucao` | Composição e aninhamento |
| Estado | `DeclaracaoVariavel`, `Tipo`, `Atribuicao` | Valores do cenário |
| Comunicação | `Envio`, `Rececao`, `ListaProcessos` | Trocas de mensagens |
| Controlo | `Condicional`, `Repeticao` | Escolha e repetição |
| Expressões | `Disjuncao` até `Primaria` | Cálculos e condições |

### Léxico

- `IDENT`: começa por letra minúscula ASCII e continua com letras ASCII, números ou `_`.
- `INT`: sequência não vazia de algarismos. O sinal negativo é um operador unário separado.
- `STRING`: conteúdo entre aspas duplas, sem aspas interiores nem quebras de linha; não há escapes nesta proposta mínima.
- Palavras reservadas: `Processes`, `Messages`, `History`, `Send`, `Recv`, `var`, `int`, `bool`, `if`, `else`, `repeat`, `true`, `false`, `and`, `or`, `not`.
- O reconhecimento deve usar palavras completas: `notavel` é um identificador, não `not` seguido de `avel`. Operadores de dois caracteres, como `>=`, devem ser reconhecidos como unidades.
- Espaços, tabulações e quebras de linha separam elementos e são ignorados entre tokens. Não podem ser removidos por concatenação prévia: `cliente servidor` deve continuar a conter dois identificadores.
- Comentários na linguagem ficam fora da versão mínima. Os comentários `(* ... *)` em `gramatica.ebnf` pertencem à documentação da gramática.
- `;` é obrigatório em declarações de variáveis e atribuições; é opcional em envios e receções, para preservar a escrita habitual existente.

### Expressões e precedência

Da maior para a menor precedência: parênteses; operadores unários `-` e `not`; multiplicação; soma/subtração; relações; igualdade; `and`; `or`.

Soma, subtração e multiplicação repetidas agrupam-se à esquerda. Assim, `8 - 3 - 1` significa `(8 - 3) - 1`. As regras de relações e igualdade admitem no máximo um operador de cada nível: `1 < 2 < 3` é rejeitado, devendo escrever-se `1 < 2 and 2 < 3`.

| Operação | Operandos | Resultado |
| --- | --- | --- |
| `+`, `-`, `*`, menos unário | `int` | `int` |
| `<`, `<=`, `>`, `>=` | `int`, `int` | `bool` |
| `==`, `!=` | Dois valores do mesmo tipo | `bool` |
| `and`, `or`, `not` | `bool` | `bool` |

## Regras semânticas propostas

Estas regras complementam a gramática. Uma frase pode ter forma correta e, mesmo assim, violar uma destas condições.

### Organização e nomes

1. No máximo um bloco de cada categoria principal. Blocos principais podem aparecer em qualquer ordem; declarações globais são recolhidas antes de analisar o histórico, como na arquitetura atual.
2. Mantém-se a possibilidade de programa vazio e blocos ausentes. Os exemplos representativos devem mostrar o domínio completo.
3. Processos não podem repetir nomes; mensagens também não.
4. Processos, mensagens, variáveis e envios pertencem a categorias de nomes distintas; o contexto sintático determina a categoria procurada.
5. Nenhuma palavra reservada pode ser usada como identificador.

### Variáveis e âmbitos

1. Uma variável exige tipo e inicializador compatível.
2. A declaração torna-se visível depois do inicializador. `var x : int := x;` não declara antecipadamente `x` para a sua própria expressão.
3. Cada bloco abre um âmbito lexical. Os nomes exteriores são visíveis nos interiores.
4. Propõe-se proibir ocultação: não se declara uma variável com o nome de outra ainda visível.
5. Uma atribuição atualiza a variável visível mais próxima; a atualização de uma variável exterior mantém-se ao sair do bloco.
6. Variáveis locais deixam de existir ao sair do bloco. Num ciclo, são recriadas a cada iteração.
7. Os valores de `int` são inteiros matemáticos nesta especificação; uma implementação deverá documentar eventuais limites.

### Condições e repetição

- `if` exige condição `bool`; só o ramo selecionado é executado. Ambos os ramos devem ser analisados estaticamente quanto a tipos e nomes, independentemente do valor inicial da condição.
- `repeat` exige expressão `int`, avaliada uma vez na entrada. O número tem de ser não negativo; zero executa zero iterações.
- Um número negativo conhecido pode ser detetado antecipadamente. Quando depender do estado, a execução deve verificar essa condição. A análise de tipos não prova a não negatividade.
- Alterar a variável usada como limite dentro do corpo não altera o número de iterações já fixado.
- Os operandos não têm efeitos laterais. Propõe-se curto-circuito para `and` e `or`.

### Comunicação

- Mensagem, emissor e destinatários devem estar declarados nas categorias corretas.
- A lista de destinatários é não vazia. Propõe-se rejeitar destinatários repetidos.
- Envio para o próprio emissor continua permitido.
- Uma receção exige um envio disponível anteriormente e só pode mencionar os seus destinatários.
- Para limitar a complexidade, o nome do envio é local ao bloco que o declara, e `Recv` só consulta envios anteriores diretamente declarados nesse mesmo bloco. Envios exteriores não são capturados por blocos interiores nesta versão mínima.
- Propõe-se rejeitar destinatários repetidos dentro de uma receção e impedir que o mesmo destinatário receba duas vezes a mesma ocorrência de envio. São decisões novas: a implementação atual aceita algumas destas duplicações. Precisam de acordo do grupo e não são pressupostos sobre o trabalho do colega.
- Receções parciais continuam permitidas: nem todos os destinatários têm de ter receção registada. A ausência representa uma entrega não registada no cenário, sem distinguir automaticamente perda, atraso ou omissão intencional.

## Base para a gramática de atributos

Esta secção é uma base formal para discussão, não uma gramática de atributos completa. A Parte I pede atributos, dependências e avaliação; campos de dataclasses e verificações Python não substituem essa especificação.

Podemos selecionar o subconjunto de declarações, âmbitos e tipos para a gramática de atributos, deixando a execução e algumas regras de comunicação especificadas separadamente.

| Atributo | Natureza | Conteúdo |
| --- | --- | --- |
| `env` | Herdado | Nomes de variáveis visíveis e respetivos tipos |
| `envOut` | Sintetizado | Ambiente de tipos depois da instrução |
| `type` | Sintetizado | Tipo calculado para uma expressão |
| `errors` | Sintetizado | Erros encontrados |
| `nome`, `valor` | Lexicais | Informação fornecida pelos tokens |

`env` é uma pilha de tabelas de tipos, não o estado de valores em execução. O valor de `concluidas` pode mudar sem mudar o seu tipo.

### Exemplos de equações

Ao expandir a EBNF, podemos usar as produções seguintes. `Erro` é um tipo especial para recuperação após um diagnóstico.

```text
Primaria → INT
  Primaria.type = int
  Primaria.errors = ∅

Primaria → true
  Primaria.type = bool
  Primaria.errors = ∅

Primaria → false
  Primaria.type = bool
  Primaria.errors = ∅

Primaria → IDENT
  Primaria.type = lookup(Primaria.env, IDENT.nome), ou Erro
  Primaria.errors = erro se o nome não existir; caso contrário ∅

Soma → Soma1 + Produto
  Soma1.env = Soma.env
  Produto.env = Soma.env
  Soma.type = int se ambos os operandos forem int; caso contrário Erro
  Soma.errors = erros dos filhos ∪ eventual erro de tipos
```

Para as outras operações, aplica-se a tabela de tipos, com propagação dos erros e do ambiente aos operandos.

```text
Declaracao → var IDENT : Tipo := Expressao ;
  Expressao.env = Declaracao.env
  valido = nome ainda não visível e Expressao.type = Tipo.type
  Declaracao.envOut = inserir(Declaracao.env, IDENT.nome, Tipo.type)
                      se valido; caso contrário Declaracao.env
  Declaracao.errors = Expressao.errors ∪ erros de declaração

Atribuicao → IDENT := Expressao ;
  Expressao.env = Atribuicao.env
  Atribuicao.envOut = Atribuicao.env
  Atribuicao.errors = Expressao.errors ∪ erros se nome ausente
                      ou tipo diferente do da expressão

Lista → Instrucao Lista1
  Instrucao.env = Lista.env
  Lista1.env = Instrucao.envOut
  Lista.envOut = Lista1.envOut
  Lista.errors = Instrucao.errors ∪ Lista1.errors

Lista → ε
  Lista.envOut = Lista.env
  Lista.errors = ∅

Bloco → { Lista }
  Lista.env = abrirAmbito(Bloco.env)
  Bloco.envOut = Bloco.env
  Bloco.errors = Lista.errors
```

A última equação devolve o ambiente de tipos exterior: as declarações locais não escapam. Não desfaz atribuições de valores, porque a execução usa um estado separado.

Para `if`, os dois blocos recebem o ambiente exterior, a condição deve ter tipo `bool` e `envOut = env`. Para `repeat`, o corpo recebe esse ambiente, a expressão deve ter tipo `int` e `envOut = env`. Declarações internas ficam confinadas aos respetivos blocos. Instruções de comunicação não acrescentam variáveis à tabela de tipos.

### Exemplo de avaliação

```text
var limite : int := 2;
var ativo : bool := limite > 0;
```

1. O literal `2` sintetiza tipo `int`.
2. A primeira declaração valida o inicializador e acrescenta `limite → int`.
3. A segunda expressão herda esse ambiente.
4. `limite` e `0` têm tipo `int`; a comparação sintetiza `bool`.
5. A declaração de `ativo` é válida e acrescenta `ativo → bool`.

Antes de entregar o relatório, é necessário completar as equações das restantes produções selecionadas, declarar os domínios dos atributos e desenhar/explicar as dependências de avaliação. Não se afirma que esta proposta já constitui essa entrega integral.

## Correspondência com os requisitos da Parte I

| Requisito | Resposta proposta |
| --- | --- |
| Finalidade específica | Descrição de cenários de comunicação |
| Variáveis e declarações | `var`, `int`, `bool` e inicializadores |
| Âmbitos | Blocos locais e regras de visibilidade |
| Expressões e estado | Operadores e atribuições |
| Composição e aninhamento | Blocos dentro de condições e ciclos |
| Decisão | `if` / `else` |
| Repetição | `repeat` |
| Semântica contextual | Tipos, nomes e relações envio/receção |
| Gramática independente de contexto | EBNF em ficheiro próprio |
| Gramática de atributos | Base de ambientes e tipagem a completar |
| Qualidade | Critérios e verificações abaixo |

O relatório e a apresentação de 10 minutos continuam a ser os produtos centrais indicados pelo enunciado. Esta pasta apoia a sua preparação; não substitui o relatório final.

## Qualidade e validação a realizar

- Clareza: justificar as palavras, os símbolos e a diferença entre mensagem, envio e receção.
- Consistência: manter a sintaxe atual; justificar `;` obrigatório apenas nas novas instruções simples.
- Expressividade: apresentar um exemplo de cada requisito sem abandonar o domínio.
- Gramática: verificar fronteiras de tokens, palavras reservadas, precedência e possíveis ambiguidades. Não foi demonstrada ausência de ambiguidades.
- Semântica: verificar tipos, âmbitos, relações de comunicação e cenários inválidos.
- Evolução: conservar identificadores e localizações nas representações internas para facilitar análises e visualizações futuras.

| Caso | Resultado esperado na extensão |
| --- | --- |
| Exemplo 01 | Aceitar, incluindo no compilador atual |
| Exemplo 02 | Aceitar após implementação; `concluidas = 2` |
| Exemplo 03 | Rejeitar: envio fora do âmbito da receção |
| Exemplo 04 | Rejeitar: atribuição bool a int |
| `repeat true { }` | Rejeitar por tipo |
| `repeat -1 { }` | Erro por limite negativo |
| `repeat 0 { ... }` | Zero iterações, mantendo análise estática do corpo |
| Uso de variável depois de sair do seu bloco | Rejeitar |
| Receção em processo que não é destinatário | Rejeitar |

Os resultados dos exemplos 02–04 são expectativas da proposta, não execuções verificadas. Os 51 testes da fotografia original passaram na análise inicial; isso não valida esta extensão.

## Nomenclatura técnica

| Termo | Definição e função neste trabalho |
| --- | --- |
| DSL | Linguagem específica de domínio: descreve cenários de mensagens |
| Léxico | Define identificadores, palavras, números, textos e símbolos |
| Token | Unidade reconhecida, como um nome ou `->` |
| Sintaxe | Define as formas permitidas das instruções |
| CFG / gramática independente de contexto | Produções que descrevem a estrutura dos programas |
| EBNF | Notação compacta com alternativas, opcionais e repetições |
| Semântica | Define significado e condições de validade |
| Análise estática | Verificações sem executar o cenário, como nomes e tipos |
| Semântica dinâmica | Comportamento ao avaliar condições, ciclos e atribuições |
| Parser | Analisador que organiza o texto segundo a gramática |
| Lark | Biblioteca já usada pelo projeto para análise |
| Earley | Algoritmo de análise usado no parser atual; não é uma garantia de ausência de ambiguidade |
| Árvore de análise | Estrutura segundo as produções reconhecidas |
| AST | Árvore de sintaxe abstrata com os conceitos relevantes |
| AST refinada | Representação elaborada após verificações e resolução de nomes |
| Âmbito lexical | Região do texto onde um nome está disponível |
| Ambiente / tabela de símbolos | Associação entre nomes e informação, como tipos |
| Estado | Associação entre variáveis e valores durante a execução |
| Atributo herdado | Informação recebida do contexto, como `env` |
| Atributo sintetizado | Informação calculada pelos componentes, como `type` |
| Dependência semântica | Relação entre atributos que determina a ordem de cálculo |
| Processo | Participante de uma comunicação |
| Mensagem | Conteúdo declarado com nome |
| Evento de envio | Acontecimento concreto que transmite uma mensagem |
| Multicast | Um envio com vários destinatários |
| Precedência | Prioridade de agrupamento dos operadores |
| Associatividade | Agrupamento de operações com igual prioridade |
| Branch | Linha de trabalho Git separada |
| Commit | Registo de uma alteração na branch |
| Pull request | Proposta de comparação e integração entre branches |
| Merge | Integração efetiva das alterações; não está incluída nesta proposta |

## Colocação no GitHub sem alterar os ficheiros existentes

Recomendação: uma branch `proposta/gramatica-manuel` e um pull request em rascunho, contendo apenas esta pasta nova. A branch principal só recebe os ficheiros se o grupo decidir integrar o pedido. Mesmo depois de integrado, este pacote apenas acrescenta documentação; não substitui código existente.

1. Abrir o repositório do grupo no GitHub e confirmar a branch principal efetiva; não presumir que se chama `main`.
2. No seletor de branches, criar `proposta/gramatica-manuel` a partir da branch acordada pelo grupo.
3. Confirmar que a branch selecionada é a da proposta.
4. Usar a opção de carregar ficheiros e colocar a pasta em `docs/propostas/gramatica-manuel/`, preservando os caminhos. Não enviar o ZIP como substituto dos ficheiros: o README deve ficar diretamente legível no GitHub.
5. Fazer commit com a mensagem `docs: adicionar proposta de gramatica de Manuel para discussao`.
6. Comparar as branches. O diff deve mostrar apenas adições sob `docs/propostas/gramatica-manuel/`; nenhum ficheiro existente deve aparecer como modificado ou removido.
7. Abrir um pull request em rascunho, quando disponível. Caso contrário, abrir um pull request normal claramente assinalado como proposta para discussão.
8. Rever com os colegas antes de qualquer merge.

Se não houver permissão para criar branches no repositório, usar um fork e abrir um pull request a partir dele. Não são necessários emails dos colegas para preparar esta proposta.

O pacote não cria branch, commit ou pull request automaticamente. Não correr `git add .` indiscriminadamente numa cópia com outras alterações: adicionar apenas a pasta da proposta. Uma versão futura da interface do GitHub pode apresentar nomes de botões diferentes; o princípio é sempre selecionar a branch da proposta e verificar o diff.

## Texto sugerido para o pull request

**Título:** `Proposta de gramática: variáveis, âmbitos e controlo de cenários Space-Time`

> Proponho uma extensão da linguagem atual para cobrir os requisitos da Parte I, mantendo Processes, Messages, History, Send e Recv. Este pedido acrescenta apenas documentação, EBNF e exemplos numa pasta independente; não altera o compilador nem os testes existentes.
>
> As novas construções ainda não estão implementadas. A proposta inclui variáveis int/bool, expressões, blocos locais, if/else e repeat, além de uma base para a gramática de atributos.
>
> Gostaria de discutir com o Pedro e o Isaías, sobretudo, o âmbito dos nomes de envios e a distinção entre uma instrução de envio e as ocorrências criadas em cada iteração. A secção final do README apresenta a regra proposta e um exemplo detalhado.
>
> Validação deste pedido: caminhos e ligações locais verificados; exemplo base executado no compilador da fotografia fornecida. Não foi validada uma implementação da extensão. A integração funcional e a gramática de atributos integral ficam dependentes do acordo do grupo.

## Discussão com Pedro e Isaías: semântica dos envios dentro de blocos e ciclos

**Intenção:** propor esta solução ao grupo, ouvir alternativas e acordar o significado antes de alterar gramática executável, AST, análise semântica ou testes.

O problema é que um nome escrito uma vez pode originar vários acontecimentos:

```text
History {
  var vezes : int := 2;

  repeat vezes {
    envio := Send(pedido) :: cliente -> servidor
    Recv(envio) :: servidor
  }
}
```

O fragmento pressupõe `cliente`, `servidor` e `pedido` declarados nos blocos globais.

Proposta de interpretação:

1. `envio` é o nome estático da instrução nesse bloco.
2. Na primeira iteração cria-se uma ocorrência de envio, que a receção dessa iteração referencia.
3. Ao terminar a iteração, o contexto local dos envios é descartado.
4. Na segunda iteração cria-se outra ocorrência, sem colisão com a primeira.
5. A nova receção referencia a ocorrência da segunda iteração.
6. Fora do ciclo, `envio` não está disponível.

| Passo | Caminho de execução | Acontecimento | Ligação |
| --- | --- | --- | --- |
| 1 | Ciclo exterior, iteração 1 | Envio de pedido | Nova ocorrência A |
| 2 | Ciclo exterior, iteração 1 | Receção no servidor | Referencia A |
| 3 | Ciclo exterior, iteração 2 | Envio de pedido | Nova ocorrência B |
| 4 | Ciclo exterior, iteração 2 | Receção no servidor | Referencia B |

A e B são rótulos explicativos, não sintaxe nova. Uma futura representação interna poderia usar `(id_do_no_AST, caminho_de_iteracoes)` para distinguir ocorrências, incluindo ciclos aninhados. Não se propõe implementar essa representação já neste pedido.

Exemplo que a regra rejeita:

```text
History {
  var ativo : bool := true;

  if ativo {
    envio := Send(pedido) :: cliente -> servidor
  }

  Recv(envio) :: servidor
}
```

O nome é local ao ramo e o envio pode não ocorrer. Uma variante mais permissiva exigiria uma análise que provasse a disponibilidade do envio em todos os caminhos; propõe-se adiar essa complexidade.

Pontos concretos para decidirmos em conjunto:

- Aceitamos nomes de envios locais ao bloco e receções apenas no mesmo bloco?
- Aceitamos recriar as ocorrências dos envios em cada iteração?
- Confirmamos que o limite de `repeat` é avaliado uma só vez à entrada?
- Rejeitamos receções duplicadas do mesmo destinatário para a mesma ocorrência?
- Mantemos permitidas entregas parciais e envios para o próprio emissor?
- Concordamos que as variáveis pertencem ao cenário global de descrição, e não automaticamente à memória de cada processo?

**Proposta de Manuel:** aprovar primeiro estas regras por consenso; depois traduzir a EBNF para Lark, completar a gramática de atributos selecionada e adaptar os módulos existentes por alterações pequenas e revistas pelo grupo.
