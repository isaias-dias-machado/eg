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

## Specification

- [`docs/semantics.md`](docs/semantics.md) — the semantic rules, in prose.
- [`spacetime/grammar.lark`](spacetime/grammar.lark) — the concrete syntax.

## Linguagem para escrever lamport space-time diagrams

Example:
```
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

  m2 := Send(ack) :: q -> p, q, r
  Recv(m2) :: p, q

  m3 := Send(request) :: r -> q
  Recv(m3) :: q
}
```


Results in:

<svg viewBox="0 0 360 320" xmlns="http://www.w3.org/2000/svg" font-family="Helvetica, Arial, sans-serif">
	<defs>
		<marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
			<path d="M0 0 L10 5 L0 10 z" fill="#d93025"/>
		</marker>
		<marker id="t" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">
			<path d="M0 0 L10 5 L0 10 z" fill="#555"/>
		</marker>
	</defs>
	<line x1="80" y1="48" x2="80" y2="285" stroke="#555" stroke-width="1.5" marker-end="url(#t)"/>
	<line x1="180" y1="48" x2="180" y2="285" stroke="#555" stroke-width="1.5" marker-end="url(#t)"/>
	<line x1="280" y1="48" x2="280" y2="285" stroke="#555" stroke-width="1.5" marker-end="url(#t)"/>
	<text x="80" y="40" text-anchor="middle" font-size="13" font-weight="bold">p</text>
	<text x="180" y="40" text-anchor="middle" font-size="13" font-weight="bold">q</text>
	<text x="280" y="40" text-anchor="middle" font-size="13" font-weight="bold">r</text>
	<line x1="85" y1="90" x2="175" y2="128" stroke="#d93025" stroke-width="1.5" marker-end="url(#a)"/>
	<text x="125" y="98" font-size="11" fill="#d93025" font-style="italic">request</text>
	<line x1="175" y1="165" x2="85" y2="208" stroke="#d93025" stroke-width="1.5" marker-end="url(#a)"/>
	<text x="118" y="178" font-size="11" fill="#d93025" font-style="italic">ack</text>
	<path d="M 186 168 C 218 172, 218 204, 186 208" fill="none" stroke="#d93025" stroke-width="1.5" marker-end="url(#a)"/>
	<line x1="185" y1="165" x2="272" y2="165" stroke="#d93025" stroke-width="1.5" stroke-dasharray="4 3" marker-end="url(#a)"/>
	<line x1="285" y1="250" x2="185" y2="268" stroke="#d93025" stroke-width="1.5" marker-end="url(#a)"/>
	<text x="235" y="252" font-size="11" fill="#d93025" font-style="italic">request</text>
	<circle cx="80" cy="90" r="5" fill="#1a73e8"/>
	<circle cx="180" cy="130" r="5" fill="#1a73e8"/>
	<circle cx="180" cy="165" r="5" fill="#1a73e8"/>
	<circle cx="80" cy="210" r="5" fill="#1a73e8"/>
	<circle cx="180" cy="210" r="5" fill="#1a73e8"/>
	<circle cx="280" cy="250" r="5" fill="#1a73e8"/>
	<circle cx="180" cy="270" r="5" fill="#1a73e8"/>
</svg>
