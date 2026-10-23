## Setup

Requires Python 3.10 or newer (developed and tested on 3.13).

Run `./setup.sh` to create the virtual environment and install the project.
It performs an editable install (`pip install --editable . --group dev`), so
`import spacetime` resolves to this checkout and the `spacetime` command is
available inside `.venv/bin/`. Dependencies live in `pyproject.toml`.

The environment lives **only** in `.venv/`. Do not create one in place at the
repository root (`python3 -m venv .`): `setup.sh` refuses to run in that
situation, and the stray `bin/`, `lib/`, `include/` and `pyvenv.cfg` would
shadow the real environment.

## Running

Compile a DSL file and print the refined AST:

```bash
source .venv/bin/activate
spacetime example.txt        # equivalently: python -m spacetime example.txt
```

To inspect every compiler stage, add `--print-stages`. It prints the Lark
parse tree, the intermediate `Ast`, and the refined AST, each under a header:

```bash
spacetime --print-stages example.txt
```

Run the test suite:

```bash
source .venv/bin/activate
pytest -q
```

## Linguagem para escrever lamport space-time diagrams

Example of the DSL at `example.txt`

Resulta em:

```dot
digraph Events {
  graph [layout=neato, splines=line, overlap=true];
  node [shape=point, width=0.09, fontname="Helvetica"];
  edge [arrowsize=0.7];

  node [shape=plaintext];
  P [label="ProcessP", pos="0,4!"];
  Q [label="ProcessQ", pos="2,4!"];
  R [label="ProcessR", pos="4,4!"];

  node [shape=point, width=0, style=invis];
  Pbot [pos="0,0!"]; Ptop [pos="0,3.7!"];
  Qbot [pos="2,0!"]; Qtop [pos="2,3.7!"];
  Rbot [pos="4,0!"]; Rtop [pos="4,3.7!"];

  node [shape=point, width=0.09, style=solid];
  p1 [pos="0,3.5!", xlabel="event1"];
  p2 [pos="2,3!", xlabel="event2"];

  // lifelines
  edge [color=black, arrowhead=none];
  Ptop -> p1 -> Pbot
  Qtop -> p2 -> Qbot
  Rtop -> Rbot

  // messages
  edge [color=blue, arrowhead=normal];
  p1 -> p2 [label="m1"]

}

```


```dot
digraph Events {
  graph [layout=neato, splines=line, overlap=true];
  node [shape=point, width=0.09, fontname="Helvetica"];
  edge [arrowsize=0.7];

  // Process labels and timeline endpoints
  node [shape=plaintext];
  P [label="Process P", pos="0,4!"];
  Q [label="Process Q", pos="3,4!"];
  R [label="Process R", pos="6,4!"];

  node [shape=point, width=0, style=invis];
  P0 [pos="0,0!"]; Ptop [pos="0,3.7!"];
  Q0 [pos="3,0!"]; Qtop [pos="3,3.7!"];
  R0 [pos="6,0!"]; Rtop [pos="6,3.7!"];

  // Six events: one send and one receive per message
  node [shape=point, width=0.09, style=solid];
  p1 [pos="0,0.5!", xlabel="p₁"];
  p2 [pos="0,3.2!", xlabel="p₂"];
  q1 [pos="3,0.8!", xlabel="q₁"];
  q2 [pos="3,2.5!", xlabel="q₂"];
  r1 [pos="6,0.5!", xlabel="r₁"];
  r2 [pos="6,3.2!", xlabel="r₂"];

  // Local process timelines: time flows upward
  edge [color=black, arrowhead=none];
  P0 -> p1 -> p2;
  Q0 -> q1 -> q2;
  R0 -> r1 -> r2;

  edge [arrowhead=normal];
  p2 -> Ptop;
  q2 -> Qtop;
  r2 -> Rtop;

  // Three messages
  edge [color="#2563eb", fontcolor="#2563eb",
        fontname="Helvetica", penwidth=1.5];
  p1 -> q2 [label="m₁"];
  q1 -> r2 [label="m₂"];
  r1 -> p2 [label="m₃"];
}
```
