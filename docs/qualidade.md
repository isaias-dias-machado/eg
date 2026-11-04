# Qualidade da linguagem e da gramática

Esta secção corresponde à tarefa 4 do enunciado (*Language and grammar quality*).
Segue o método do notebook NB07 (*Language and Grammar Quality*, Nuno Macedo,
com base na lição de P. R. Henriques):

1. avaliar a **linguagem** pelos oito fatores internos de qualidade (NB07, §7.1);
2. avaliar a **gramática** pelas suas características de usabilidade e de
   eficiência, medidas com métricas de tamanho, forma e léxico (NB07, §7.2).

O objeto avaliado é a linguagem definida por `spacetime/grammar.lark` (sintaxe)
e pelas regras semânticas de `semantic.spec`, verificadas pelo compilador. As
métricas são calculadas por `docs/metricas_gramatica.py`, que reutiliza o código
do NB07. Para as reproduzir:

```bash
python docs/metricas_gramatica.py
```

## 1. Qualidade da linguagem

A linguagem descreve cenários de comunicação entre processos, para serem
representados como diagramas espaço-tempo de Lamport. Um programa declara
processos e mensagens e regista uma história de envios e receções:

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

O compilador verifica o programa e produz uma representação resolvida. O
desenho do diagrama fica para a Parte II.

### 1.1 Expressividade

- (+) Cada construção corresponde a um conceito do domínio: `Processes` às
  linhas dos processos, `Messages` às mensagens trocadas, `Send` e `Recv` aos
  eventos de envio e de receção.
- (+) Os padrões frequentes escrevem-se de forma compacta. Um envio pode ter
  vários destinatários (`m2 := Send(ack) :: q -> p, q, r`). Cada mensagem é
  declarada uma vez e reutilizada pelo nome.
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
  comentada (com um exemplo de cada evento), pela lista de regras semânticas
  (`semantic.spec`) e por um exemplo com o diagrama correspondente (README).

**Efeito:** a falta de comentários prejudica a compreensão de cenários grandes.

### 1.3 Unicidade

- (+) Há uma única forma de declarar um processo, uma mensagem, um envio e
  uma receção.
- (−) O programa não tem uma forma única. Os três blocos são opcionais e
  podem aparecer por qualquer ordem, e as mudanças de linha não têm
  significado: `Processes { p q }` é válido, tal como vários blocos na mesma
  linha ou um evento partido em várias linhas.
- (−) Duas escritas parecidas têm significados diferentes. `Recv(m2) :: p, q`
  é **um** evento, enquanto `Recv(m2) :: p` seguido de `Recv(m2) :: q` são
  **dois** eventos, em posições temporais diferentes (ver o comentário de
  `recv_event` em `spacetime/grammar.lark`).

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

- (+) O compilador verifica estaticamente as regras semânticas (`semantic.spec`,
  `spacetime/builder.py` e `spacetime/semantics.py`):
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
são estáticas: correm uma vez, ao compilar o programa.

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
| Expressividade | Média | As construções são os conceitos do diagrama, mas faltam os eventos internos |
| Documentação | Baixa | Não há comentários; só o texto das mensagens |
| Unicidade | Média | Cada construção tem uma só forma, mas a ordem dos blocos e o layout são livres, e uma receção conjunta difere de receções separadas |
| Consistência | Alta, com exceções | `:=`, `::` e `->` são uniformes; `Send` e `Recv` são assimétricos |
| Extensibilidade | Baixa | Não há mecanismos de extensão |
| Escalabilidade | Baixa | O programa cresce linearmente, sem repetição, e os nomes são globais |
| Fiabilidade | Alta | As regras estão definidas e são verificadas, com a posição de cada erro; a análise para no primeiro erro |
| Modularidade | Baixa | Não há importação; os blocos só separam declarações e história |

## 2. Qualidade da gramática

O NB07 avalia a gramática como artefacto para pessoas (usabilidade:
compreensão, derivação, manutenção) e como entrada de ferramentas (eficiência:
reconhecimento, geração). Primeiro apresentamos as métricas e depois a
caracterização que delas resulta.

Os valores são os da gramática atual. A própria avaliação levou a corrigir a
versão anterior, como se explica em 2.4.

### 2.1 Métricas de tamanho

| Métrica | Valor | Observação |
|---|---|---|
| Terminais | 16 | 15 usados nas regras, mais o espaço ignorado |
| Não-terminais | 25 | 20 escritos, mais 5 auxiliares gerados a partir do EBNF |
| Produções | 38 | |
| Produções unitárias (A → B) | 15 | 3 vêm de `_block` e 2 de `event`; as restantes, de listas e de `start` |
| Não-terminais diretamente recursivos | 5 | ver 2.2 |
| Não-terminais indiretamente recursivos | 0 | |
| Comprimento do lado direito (média / máx.) | 1,76 / 10 | o máximo é `send_event` |
| Produções por não-terminal (média / máx.) | 1,52 / 3 | o máximo é `_block` |
| Subgramáticas importadas | 0 | |
| Grau de entrada / saída médio | 1,32 / 1,32 | grafo de dependências entre não-terminais |
| Estados LALR / entradas da tabela | 63 / 178 | |

Para comparação, a gramática de expressões usada como exemplo no NB07 tem
10 terminais, 6 não-terminais, 12 produções e uma tabela LALR de 25 estados e
85 entradas. A nossa gramática é entre 1,6 e 4,2 vezes maior, conforme a
métrica, mas continua pequena.

Há ainda 6 regras da forma `X → IDENTIFIER` ou `X → STRING`
(`process_declaration`, `message_name`, `message_identifier`,
`event_identifier`, `process_identifier`, `message_value`). Não contam como
unitárias, porque o lado direito é um terminal. Servem para dar a cada nome o
seu papel (declaração ou referência, processo, mensagem ou evento).

### 2.2 Métricas de forma

- **Forma da recursão:** só há recursão direta.
- **Tipo de recursão:** é uniforme. As 5 regras recursivas são auxiliares que o
  Lark gera a partir de `*`, todas recursivas à esquerda. Nenhuma regra escrita
  é recursiva.
- **Notação:** usa as duas. 5 regras usam EBNF (`*`) e 15 são BNF puro, mas de
  forma coerente: a repetição escreve-se sempre com `*`. O NB07 nota que o uso
  inconsistente da notação prejudica a legibilidade, o que aqui não acontece.

### 2.3 Métricas lexicográficas

- **Clareza dos identificadores:** os 20 não-terminais têm nomes derivados de
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
- **Terminais flexíveis:** 3 flexíveis (`IDENTIFIER`, `STRING` e o espaço
  ignorado) e 13 fixos (5 palavras-chave, 3 operadores e 5 sinais de
  pontuação). Os flexíveis têm restrições: `IDENTIFIER` tem de começar por
  minúscula (um processo `Alice` é rejeitado), e `STRING` não tem sequências de
  escape, não pode conter `"` nem mudar de linha.
- **Comentários:** não há comentários de linha, de bloco nem com
  meta-informação.

### 2.4 Reconhecimento: conflitos e ambiguidade

Esta verificação vai além das métricas do NB07, mas mede diretamente a
característica de reconhecimento. Foi também o que deu origem à principal
alteração da gramática.

Na versão anterior, as mudanças de linha eram tratadas por uma regra que podia
ser vazia, `_newlines`, usada 11 vezes em 7 regras e por vezes em posições
adjacentes:

```
history_block : _HISTORY "{" _newlines _event_list _newlines "}"
event         : send_event _newlines | recv_event _newlines
```

As mudanças de linha depois do último evento tanto podiam ser derivadas pelo
evento como pelo bloco, e o mesmo acontecia entre blocos. Construída como
LALR(1), essa gramática tinha **9 conflitos shift/reduce, todos na mudança de
linha**, que o Lark resolvia sem avisar. Com `ambiguity="explicit"`, o Earley
encontrava nós ambíguos em **7 dos 8 exemplos válidos**. A árvore final não era
afetada, porque as mudanças de linha são descartadas, mas o defeito ficava
escondido.

A correção foi tratar a mudança de linha como espaço (`%ignore /[ \t\n]/`) e
remover `_newlines`. O mesmo script mediu o resultado (os valores de antes são
os do commit `6e93331`):

| Métrica | Antes | Depois |
|---|---|---|
| Conflitos LALR(1) | 9 | 0 |
| Exemplos válidos com ambiguidade | 7 de 8 | 0 de 8 |
| Regras escritas | 21 | 20 |
| Terminais | 17 | 16 |
| Produções (compiladas) | 40 | 38 |
| Produções unitárias | 10 | 15 |
| Grau de entrada / saída médio | 1,58 | 1,32 |
| Estados / entradas LALR | 80 / 290 | 63 / 178 |
| Tipo de recursão | Direita e esquerda | Só esquerda (gerada) |

Os 8 exemplos válidos produzem exatamente a mesma árvore e os 51 testes
continuam a passar. A gramática deixou de ter conflitos LALR(1), o que garante
que não é ambígua. O custo é pequeno: as produções unitárias sobem, porque
`event → send_event` e as listas deixaram de ter `_newlines`. A linguagem mudou
num ponto: passou a ser possível mudar de linha dentro de um evento, por
exemplo para partir uma lista longa de destinatários.

### 2.5 Caracterização da gramática independente de contexto

| Elemento (NB07) | Na nossa gramática | Efeito segundo o NB07 |
|---|---|---|
| Identificadores claros | 20 de 20 derivados de conceitos; 4 abreviaturas; 2 inconsistências | Favorece compreensão, derivação e manutenção |
| Produções unitárias | 15, mais 6 regras que dão papel aos nomes | Favorecem compreensão e manutenção; prejudicam derivação e eficiência |
| Comprimento das produções | Média de 1,76; `send_event` tem 10 símbolos | As regras longas são mais difíceis de ler; `send_event` segue a ordem da sintaxe concreta |
| Notação | EBNF nas listas e BNF no resto, de forma coerente | Só o uso inconsistente prejudica a compreensão |
| Recursão | Só direta, à esquerda e gerada pelo Lark; nenhuma regra escrita é recursiva | A recursão à esquerda dificulta a derivação, mas aqui fica escondida pelo `*` |
| Modularidade | Um ficheiro, 0 importações | Pouco relevante numa gramática de 20 regras |
| Complexidade sintática | Grau médio 1,32; sem recursão indireta; máx. 3 alternativas | Baixa, o que favorece a manutenção |

- **Compreensão:** os nomes e os comentários da gramática (secções e um
  exemplo de cada evento) ajudam. A regra longa de `send_event` prejudica.
- **Derivação:** as listas em EBNF são compactas, e cada texto tem uma só
  derivação.
- **Manutenção:** as dependências são simples. Como a mudança de linha é
  tratada como espaço, as novas construções não têm de a prever.
- **Reconhecimento:** a gramática já não precisa de um parser geral. O projeto
  continua a usar Earley, que no pior caso é cúbico, mas pode passar a LALR(1),
  que é linear (ver secção 4).
- **Geração:** a tabela LALR teria 63 estados e 178 entradas, uma dimensão
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
  auxiliares do EBNF aumentam as contagens (20 regras escritas contra 25
  não-terminais).
- A clareza dos identificadores e das palavras-chave é um juízo nosso, não
  uma medida automática.
- A tabela LALR é uma aproximação, porque o projeto usa Earley.
- Como lembra o NB07 (*Beyond metrics*), as métricas dão uma visão parcial.
  Os efeitos na aprendizagem e na escrita são hipóteses. Para os confirmar,
  seria preciso um estudo com utilizadores, por exemplo pedir a colegas que
  escrevam um cenário e medir o tempo e os erros.

## 4. Propostas de melhoria

A principal melhoria, a eliminação da ambiguidade, já foi aplicada (ver 2.4).
Ficam estas, por ordem de prioridade:

1. **Comentários de linha** (por exemplo `// ...`, com
   `COMMENT: /\/\/[^\n]*/` e `%ignore COMMENT`). Melhora a documentação com
   apenas mais um terminal, sem efeito na árvore.
2. **Reportar todos os erros semânticos** em vez de parar no primeiro.
   Melhora a fiabilidade na prática e a escrita.
3. **Nomes consistentes na gramática**, por exemplo `message_decl` passa a
   `message_declaration`, e os nomes declarados de processos e mensagens
   passam a seguir o mesmo padrão. Implica renomear os métodos
   correspondentes em `spacetime/builder.py`.
4. **Passar o parser a LALR(1)** (`parser="lalr"`), que é linear. A gramática
   já o permite: 50 dos 51 testes passam, e o que falha é o da posição do erro
   de fim de ficheiro, que exige um pequeno ajuste.
5. **Mais expressividade e escalabilidade:** eventos internos e mecanismos de
   repetição e de parametrização (a extensão discutida no grupo, com
   variáveis, `if` e `repeat`).

## 5. Conclusão

A linguagem é pequena, consistente e próxima do domínio. Exprime bem cenários
pequenos e tem uma análise semântica fiável, que indica a posição de cada
erro. Os pontos fracos são a documentação (não há comentários), a
escalabilidade e a modularidade (não há abstração nem reutilização). Na
gramática, a avaliação encontrou um problema no tratamento das mudanças de
linha, que a tornava ambígua (9 conflitos LALR e ambiguidade em 7 dos 8
exemplos). A correção foi uma alteração local, verificada com as mesmas
métricas: a gramática atual é LALR(1), sem conflitos, e produz as mesmas
árvores com uma tabela 39% mais pequena.
