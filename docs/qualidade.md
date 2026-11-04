# Qualidade da linguagem e da gramática

Esta secção corresponde à tarefa 4 do enunciado (*Language and grammar quality*).
Segue o método do notebook NB07 (*Language and Grammar Quality*, Nuno Macedo,
com base na lição de P. R. Henriques):

1. avaliar a **linguagem** pelos oito fatores internos de qualidade (NB07, §7.1);
2. avaliar a **gramática** pelas suas características de usabilidade e de
   eficiência, medidas com métricas de tamanho, forma e léxico (NB07, §7.2).

O objeto avaliado é a linguagem definida por `spacetime/grammar.lark` (sintaxe)
e por `docs/semantics.md` (regras semânticas). As métricas são calculadas por
`docs/metricas_gramatica.py`, que reutiliza o código do NB07. Para as reproduzir:

```bash
python docs/metricas_gramatica.py
```

## 1. Qualidade da linguagem

A linguagem descreve cenários de comunicação entre processos, para gerar
diagramas espaço-tempo de Lamport. Um programa declara processos e mensagens e
regista uma história de envios e receções:

```
Processes {
  p
  q
}

Messages {
  request := "Request"
}

History {
  m1 := Send(request) :: p -> q
  Recv(m1) :: q
}
```

### 1.1 Expressividade

- (+) Cada construção corresponde a um conceito do domínio: `Processes` às
  linhas dos processos, `Messages` às mensagens trocadas, `Send` e `Recv` aos
  eventos de envio e de receção.
- (+) Os padrões frequentes escrevem-se de forma compacta. Um envio pode ter
  vários destinatários (`m2 := Send(ack) :: q -> p, q, r`). Cada mensagem é declarada uma
  vez e reutilizada pelo nome.
- (−) Falta um conceito do domínio: os diagramas de Lamport têm também
  eventos internos (locais), que a linguagem não representa.

**Efeito:** favorece a aprendizagem, a escrita e a compreensão de cenários
pequenos. Não afeta o desempenho.

### 1.2 Documentação

- (−) A linguagem não tem comentários: `# nota`, `// nota` e `/* nota */` são
  rejeitados pelo parser (verificado pelo script). Não é possível explicar,
  dentro do programa, o objetivo de um cenário ou de uma mensagem.
- (+) O conteúdo de cada mensagem (`request := "Request o que quiser"`) é
  texto livre e funciona como uma descrição embutida.
- (+) Fora dos programas, a linguagem está documentada pela gramática
  comentada (com um exemplo de cada evento), pelas regras semânticas em prosa
  (`docs/semantics.md`) e por um exemplo com o diagrama correspondente (README).

**Efeito:** a falta de comentários prejudica a compreensão de cenários grandes.

### 1.3 Unicidade

- (+) Há uma única forma de declarar um processo, uma mensagem, um envio e
  uma receção.
- (−) O programa não tem uma forma única. Os três blocos são opcionais e
  podem aparecer por qualquer ordem, e as mudanças de linha são livres:
  `Processes { p q }` é válido, tal como vários blocos na mesma linha.
- (−) Duas escritas parecidas têm significados diferentes. `Recv(m2) :: p, q`
  é **um** evento, enquanto `Recv(m2) :: p` seguido de `Recv(m2) :: q` são
  **dois** eventos, em posições temporais diferentes (`docs/semantics.md`,
  secção *Result*).

**Efeito:** a forma única de cada construção ajuda a aprendizagem e a
compreensão. A ordem livre facilita a escrita, mas dificulta comparar
programas escritos por pessoas diferentes.

### 1.4 Consistência

- (+) As convenções são uniformes. As definições usam sempre `nome := valor`
  (mensagens e envios), `::` introduz sempre os processos onde o evento
  ocorre, `->` introduz os destinatários e os blocos têm sempre a forma
  `Palavra { ... }`. As palavras-chave começam por maiúscula e os nomes por
  minúscula, por isso nenhum nome escolhido pelo utilizador colide com uma
  palavra-chave.
- (−) `Send` e `Recv` são assimétricos. O envio dá nome ao evento
  (`m1 := Send(...)`) e a receção não. `Send` é uma palavra completa e `Recv`
  uma abreviatura. Depois de `::`, `Send` aceita um só processo e `Recv` uma
  lista.
- (−) Na mesma posição, entre parênteses, `Send(request)` recebe uma
  *mensagem* e `Recv(m1)` recebe um *evento*. É fácil escrever
  `Recv(request)` por engano (o erro é detetado, ver 1.7).

**Efeito:** as convenções uniformes ajudam a aprendizagem, a escrita e a
compreensão. As exceções têm de ser memorizadas. Não afeta o desempenho.

### 1.5 Extensibilidade

- (−) Não há extensão léxica nem semântica: o utilizador não pode definir
  tipos, macros, abreviaturas ou novos tipos de evento.
- (+) O conteúdo das mensagens não é interpretado. Pode por isso transportar
  informação do domínio sem alterar a gramática.

**Efeito:** a simplicidade favorece a aprendizagem. A falta de mecanismos de
extensão limita a escrita de cenários mais ricos.

### 1.6 Escalabilidade

- (−) O tamanho de um programa cresce linearmente com o número de eventos e
  não há forma de fatorizar repetições. Por exemplo, um protocolo de *k*
  rondas em que cada um de *n* processos envia uma mensagem a todos os outros
  precisa de *k·n* envios e *k·n* receções (2·*k*·*n* linhas), e cada envio
  precisa de um nome único.
- (−) Todos os nomes são globais e os nomes dos envios têm de ser únicos em
  toda a história, o que torna a gestão de nomes pesada em histórias longas.
- (+) Os envios com vários destinatários e as receções conjuntas reduzem o
  número de linhas.

**Efeito:** a escrita e a compreensão degradam-se à medida que o cenário cresce.

### 1.7 Fiabilidade

- (+) A semântica está definida (`docs/semantics.md`) e é verificada
  estaticamente antes de gerar o diagrama:
  - cada bloco aparece no máximo uma vez;
  - os nomes de processos, de mensagens e de envios são únicos;
  - a mensagem, o emissor e os destinatários de um envio estão declarados;
  - cada receção refere um envio anterior e só ocorre em destinatários desse
    envio.
- (+) Os erros semânticos indicam o nome em causa e a sua posição no ficheiro
  (`SemanticError`). Os erros de sintaxe mostram um excerto do código
  (`ParseError`).
- (−) A análise para no primeiro erro (`spacetime/semantics.py` lança a
  exceção logo que o encontra). Corrigir vários erros obriga a várias
  execuções.

**Efeito:** as restrições explícitas melhoram a compreensão. As verificações
são estáticas, feitas uma vez antes de gerar o diagrama.

### 1.8 Modularidade

- (−) Não há módulos, importações nem partes de cenários reutilizáveis: cada
  ficheiro é um cenário fechado.
- (+) Dentro de um programa, os blocos separam as declarações (`Processes`,
  `Messages`) do comportamento (`History`).

**Efeito:** chega para cenários pequenos, mas impede reutilizar partes comuns
entre cenários.

### 1.9 Síntese

| Fator | Avaliação | Razão principal |
|---|---|---|
| Expressividade | Média | As construções são os conceitos do diagrama, mas faltam os eventos internos e a abstração |
| Documentação | Baixa | Não há comentários; só o texto das mensagens |
| Unicidade | Média | Cada construção tem uma só forma, mas a ordem dos blocos e o layout são livres, e uma receção conjunta difere de receções separadas |
| Consistência | Alta, com exceções | `:=`, `::` e `->` são uniformes; `Send` e `Recv` são assimétricos |
| Extensibilidade | Baixa | Não há mecanismos de extensão; a extensão sintática é localizada |
| Escalabilidade | Baixa | O programa cresce linearmente, sem repetição, e os nomes são globais |
| Fiabilidade | Alta | As regras estão definidas e são verificadas, com a posição de cada erro; a análise para no primeiro erro |
| Modularidade | Baixa | Não há importação; os blocos só separam declarações e história |

## 2. Qualidade da gramática

O NB07 avalia a gramática como artefacto para pessoas (usabilidade:
compreensão, derivação, manutenção) e como entrada de ferramentas (eficiência:
reconhecimento, geração). Primeiro apresentamos as métricas e depois a
caracterização que delas resulta.

### 2.1 Métricas de tamanho

| Métrica | Valor | Observação |
|---|---|---|
| Terminais | 17 | 16 usados nas regras, mais o espaço ignorado |
| Não-terminais | 26 | 21 escritos, mais 5 auxiliares gerados a partir do EBNF |
| Produções | 40 | |
| Produções unitárias (A → B) | 10 | 3 vêm de `_block`; as restantes, de listas e de `start` |
| Não-terminais diretamente recursivos | 6 | ver 2.2 |
| Não-terminais indiretamente recursivos | 0 | |
| Comprimento do lado direito (média / máx.) | 2,1 / 10 | o máximo é `send_event` |
| Produções por não-terminal (média / máx.) | 1,54 / 3 | o máximo é `_block` |
| Subgramáticas importadas | 0 | |
| Grau de entrada / saída médio | 1,58 / 1,58 | grafo de dependências entre não-terminais |
| Estados LALR / entradas da tabela | 80 / 290 | |

Para comparação, a gramática de expressões usada como exemplo no NB07 tem
10 terminais, 6 não-terminais, 12 produções e uma tabela LALR de 25 estados e
85 entradas. A nossa gramática é cerca de três vezes maior, mas continua
pequena.

Há ainda 6 regras da forma `X → IDENTIFIER` ou `X → STRING`
(`process_declaration`, `message_name`, `message_identifier`,
`event_identifier`, `process_identifier`, `message_value`). Não contam como
unitárias, porque o lado direito é um terminal. Servem para dar a cada nome o
seu papel (declaração ou referência, processo, mensagem ou evento).

### 2.2 Métricas de forma

- **Forma da recursão:** só há recursão direta.
- **Tipo de recursão:** é mista. `_newlines`, escrita na gramática, é
  recursiva à direita. As 5 regras auxiliares que o Lark gera a partir de `*`
  são recursivas à esquerda.
- **Notação:** é mista. 5 regras usam EBNF (`*`) e 16 são BNF puro. A
  repetição é escrita de duas maneiras: com `*` nas listas e com recursão BNF
  em `_newlines`. O NB07 nota que o uso inconsistente da notação prejudica a
  legibilidade.

### 2.3 Métricas lexicográficas

- **Clareza dos identificadores:** os 21 não-terminais têm nomes derivados de
  conceitos do domínio ou da estrutura (`processes_block`, `send_event`,
  `process_list`, ...). 4 usam abreviaturas (`decl` em três, `recv` em um). Há
  2 inconsistências: `message_decl` abrevia o que `process_declaration`
  escreve por extenso, e o nome declarado chama-se `message_name` nas
  mensagens mas `process_declaration` nos processos.
- **Clareza das palavras-chave:** as 5 palavras-chave (`Processes`,
  `Messages`, `History`, `Send`, `Recv`) derivam do conceito que representam;
  só `Recv` é abreviada. Dos 3 operadores, `:=` (definição) e `->` (destino)
  são convencionais. `::` (processo onde ocorre o evento) não deriva de um
  conceito e tem outros significados noutras linguagens (tipos em Haskell,
  âmbito em C++).
- **Terminais flexíveis:** 4 flexíveis (`IDENTIFIER`, `STRING`, a mudança de
  linha `_NL` e o espaço ignorado) e 13 fixos (5 palavras-chave, 3 operadores e
  5 sinais de pontuação). Os flexíveis têm restrições: `IDENTIFIER` tem de
  começar por minúscula (um processo `Alice` é rejeitado), e `STRING` não tem
  sequências de escape, não pode conter `"` nem mudar de linha.
- **Comentários:** não há comentários de linha, de bloco nem com
  meta-informação.

### 2.4 Reconhecimento: conflitos e ambiguidade

Esta verificação vai além das métricas do NB07, mas mede diretamente a
característica de reconhecimento.

O projeto usa o algoritmo de Earley (`spacetime/parser.py`). Se a mesma
gramática for construída como LALR(1), o Lark encontra **9 conflitos
shift/reduce, todos no terminal `_NL`**, e resolve-os sem avisar (escolhe
*shift*).

A causa é `_newlines`: pode ser vazia e aparece em posições adjacentes. Por
exemplo, em

```
history_block : _HISTORY "{" _newlines _event_list _newlines "}"
event         : send_event _newlines | recv_event _newlines
```

as mudanças de linha depois do último evento tanto podem ser derivadas pelo
evento como pelo bloco. Acontece o mesmo entre blocos
(`(_newlines _block _newlines)*`) e em `messages_block`. `processes_block` não
tem o `_newlines` final, o que também torna inconsistentes três blocos que
deviam ter a mesma forma.

Com `ambiguity="explicit"`, o Earley encontra nós ambíguos em **7 dos 8
exemplos válidos** (de 1 a 3 por ficheiro); só o programa vazio não tem
nenhum. A gramática é portanto ambígua. A árvore final não é afetada, porque
as mudanças de linha são descartadas, mas o defeito fica escondido e impede o
uso de um parser LALR(1), que seria linear.

Além disso, `_newlines` nunca torna uma mudança de linha obrigatória, porque
pode ser vazia (`Processes { p q }` é válido). Na prática, só impede que haja
mudanças de linha dentro de um evento.

### 2.5 Caracterização da gramática independente de contexto

| Elemento (NB07) | Na nossa gramática | Efeito segundo o NB07 |
|---|---|---|
| Identificadores claros | 21 de 21 derivados de conceitos; 4 abreviaturas; 2 inconsistências | Favorece compreensão, derivação e manutenção |
| Produções unitárias | 10, mais 6 regras que dão papel aos nomes | Favorecem compreensão e manutenção; prejudicam derivação e eficiência |
| Comprimento das produções | Média de 2,1; `send_event` tem 10 símbolos | As regras longas são mais difíceis de ler; `send_event` segue a ordem da sintaxe concreta |
| Notação | Mista (EBNF e BNF) | O uso inconsistente prejudica a compreensão |
| Recursão | Só direta; à direita (`_newlines`) e à esquerda (gerada) | A recursão à direita favorece a derivação |
| Modularidade | Um ficheiro, 0 importações | Pouco relevante numa gramática de 21 regras |
| Complexidade sintática | Grau médio 1,58; sem recursão indireta; máx. 3 alternativas | Baixa, o que favorece a manutenção |

- **Compreensão:** os nomes e os comentários da gramática (secções e um
  exemplo de cada evento) ajudam. A notação mista e a regra longa de
  `send_event` prejudicam.
- **Derivação:** as listas em EBNF são compactas, mas a ambiguidade faz com
  que o mesmo texto tenha várias derivações.
- **Manutenção:** as dependências são simples. O ponto fraco é `_newlines`,
  que aparece 11 vezes em 7 regras: cada nova construção tem de o colocar no
  sítio certo, e a ambiguidade atual mostra como é fácil errar.
- **Reconhecimento:** por causa dos conflitos, é preciso um parser geral
  (Earley), que no pior caso é cúbico, em vez de um LALR(1), que é linear.
- **Geração:** a tabela LALR teria 80 estados e 290 entradas, uma dimensão
  pequena.

### 2.6 Gramática de atributos

As métricas de gramáticas de atributos do NB07 aplicam-se à gramática de
atributos da tarefa 3: número de atributos herdados e sintetizados, regras de
avaliação, condições de contexto, grafo de dependências, complexidade dos
atributos e clareza dos identificadores. Ficam por aplicar até essa gramática
estar escrita. O código atual (`spacetime/builder.py` e
`spacetime/semantics.py`) faz as verificações em Python, de forma
procedimental, e por isso não permite extrair estas métricas.

## 3. Limitações da avaliação

- As métricas são calculadas sobre a gramática compilada pelo Lark. As regras
  auxiliares do EBNF aumentam as contagens (21 regras escritas contra 26
  não-terminais).
- A clareza dos identificadores e das palavras-chave é um juízo nosso, não
  uma medida automática.
- A tabela LALR é uma aproximação, porque o projeto usa Earley.
- Como lembra o NB07 (*Beyond metrics*), as métricas dão uma visão parcial.
  Os efeitos na aprendizagem e na escrita são hipóteses. Para os confirmar,
  seria preciso um estudo com utilizadores, por exemplo pedir a colegas que
  escrevam um cenário e medir o tempo e os erros.

## 4. Propostas de melhoria

Por ordem de prioridade:

1. **Eliminar a ambiguidade das mudanças de linha.** Tratar a mudança de
   linha como espaço (`%ignore /[ \t\r\n]/`) e remover `_NL`, `_newlines` e as
   suas 11 utilizações. Medimos esta variante com o mesmo script:

   | Métrica | Atual | Proposta |
   |---|---|---|
   | Conflitos LALR(1) | 9 | 0 |
   | Exemplos válidos com ambiguidade | 7 de 8 | 0 de 8 |
   | Regras escritas | 21 | 20 |
   | Terminais | 17 | 16 |
   | Produções (compiladas) | 40 | 38 |
   | Estados / entradas LALR | 80 / 290 | 63 / 178 |
   | Tipo de recursão | Direita e esquerda | Só esquerda (gerada) |

   Os 8 exemplos válidos produzem exatamente a mesma árvore que hoje, e o
   exemplo com erro de sintaxe continua a ser rejeitado. A única diferença na
   linguagem é que passa a ser possível mudar de linha dentro de um evento
   (por exemplo, para partir uma lista longa de destinatários), o que hoje é
   um erro. Depois desta mudança, o parser pode passar a LALR(1)
   (`parser="lalr"`).
2. **Comentários de linha** (por exemplo `// ...`, com
   `COMMENT: /\/\/[^\n]*/` e `%ignore COMMENT`). Melhora a documentação com
   apenas mais um terminal, sem efeito na árvore.
3. **Reportar todos os erros semânticos** em vez de parar no primeiro.
   Melhora a fiabilidade na prática e a escrita.
4. **Nomes consistentes na gramática**, por exemplo `message_decl` passa a
   `message_declaration`, e os nomes declarados de processos e mensagens
   passam a seguir o mesmo padrão. Implica renomear os métodos
   correspondentes em `spacetime/builder.py`.
5. **Mais expressividade e escalabilidade:** eventos internos e mecanismos de
   repetição e de parametrização (a extensão discutida no grupo, com
   variáveis, `if` e `repeat`).

## 5. Conclusão

A linguagem é pequena, consistente e próxima do domínio. Exprime bem cenários
pequenos e tem uma análise semântica fiável, que indica a posição de cada
erro. Os pontos fracos são a documentação (não há comentários), a
escalabilidade e a modularidade (não há abstração nem reutilização). Na
gramática, o problema principal é o tratamento das mudanças de linha. Torna a
gramática ambígua (9 conflitos LALR e ambiguidade em 7 dos 8 exemplos) e
obriga a usar um parser geral. A primeira proposta resolve este problema com
uma alteração local, verificada com as mesmas métricas.
