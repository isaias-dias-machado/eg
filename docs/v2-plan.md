# v2 plan — refined AST for the `Maybe` block

## Goal and scope

v2 of the space-time DSL adds a `Maybe` block that groups several history
events into one optional branch. The goal of the language change is to enable
CFG (control-flow graph) construction and static checking.

**This phase delivers the front end only, up to the refined AST:**
parse → `Ast` → `RefinedAst` with a tree-shaped history.

**Out of scope for this phase:** graph generation and static checks. In the
next phase we walk the refined tree *by hand* and build the graph manually,
so that we understand how it is done, before codifying it.

## Branch and layout

- Branch `v2`, worktree `~/.vibe/worktrees/source-4d0a4dff1f76/v2-refined-ast`.
- v1 stays untouched: `spacetime/grammar.lark`, `ast.py`, `builder.py`,
  `semantics.py` and the v1 fixtures keep working as they are.
- New subpackage `spacetime/v2/`:
  - `grammar.lark` — v1 grammar plus the `Maybe` block
  - `ast.py` — v1 nodes plus `MaybeBlock` / `HistoryItem`
  - `builder.py` — same Lark `Interpreter` pattern as v1
  - `resolve.py` — name resolution and validation, `Ast` → `RefinedAst`
  - `__init__.py` — exposes `compile_source` / `compile_file`
- Shared modules, generalized in a v1-compatible way:
  - `parser.py` — `_get_parser(grammar_path)` cached per grammar file
  - `render.py` — render the new `items` field
  - `compiler.py` / `cli.py` — a `--v2` flag selects the v2 pipeline
- Fixtures under `tests/fixtures/v2/{valid,invalid}/`, tests in
  `tests/test_v2_*.py`, parametrized like the existing suites.

## Concrete syntax

```
History {
  m1 := Send(request) :: p -> q
  Maybe {
    m2 := Send(ack) :: q -> p
    Recv(m2) :: p
  }
  Recv(m1) :: q
}
```

New grammar rules:

```
history_block : _HISTORY "{" history_item* "}"
history_item  : event | maybe_block
maybe_block   : _MAYBE "{" history_item* "}"
```

- `_MAYBE : "Maybe"` — capitalized keyword, so it can never collide with
  `IDENTIFIER` (which must start lowercase), same convention as
  `Processes` / `Messages` / `History`.
- Nesting is allowed because `maybe_block` is recursive.
- Newlines stay `%ignore`d. Never introduce a `_newlines` rule: that is what
  caused the 9 LALR conflicts in v1 (see `docs/qualidade.md` §2.4). The v2
  grammar must stay conflict-free; `docs/metricas_gramatica.py` can be rerun
  on it later.

## Raw AST (`spacetime/v2/ast.py`)

- `History.items: list[HistoryItem]` where
  `HistoryItem = SendEvent | RecvEvent | MaybeBlock`.
- `MaybeBlock(items: list[HistoryItem], location: SourceLocation)`.
- `SendEvent`, `RecvEvent`, and the declaration nodes are unchanged from v1.

## Refined AST — the deliverable of this phase

- `HistoryRefined.items: list[SendEventRefined | RecvEventRefined | MaybeBlockRefined]`.
- `MaybeBlockRefined(items)` — no name and no position of its own.
- Events keep `temporal_pos` as the **global** 0-based index over the
  flattened, source-order event sequence (flattening walks `Maybe` blocks
  depth-first). The tree keeps the branch structure; `temporal_pos` gives the
  later CFG walk a total order over events.
- `resolve.py` is v1 `semantics.py` adapted to the tree. Same checks:
  duplicate blocks / declarations / event names, undeclared message, process
  or send event, and linear causality (`seen_sends` threaded through the
  flattened order, as in v1). One v1 check is **dropped**: recipient
  membership. A `Recv` may name any declared process; at a non-recipient it
  just means the message was not received there (see
  `tests/fixtures/v2/valid/recv_not_recipient_in_maybe.st`).
- **Known limitation, to be fixed by the CFG walk in the next phase:** linear
  causality accepts a `Recv(m)` outside a `Maybe` whose `Send(m)` is inside
  it. The CFG check will tighten this to dominance: a receive is legal only
  on paths where the send actually happened.

## Pipeline wiring

- `parser._get_parser(grammar_path)` cached per grammar file; the v1 default
  is unchanged.
- `spacetime.v2.compile_source(source)` returns the v2 `RefinedAst`, with the
  same `observe` stage hook (`"parse"`, `"ast"`, `"refined"`).
- CLI: `spacetime --v2 FILE [--print-stages]`.
- `render.py`: the generic dataclass renderer already handles new node types;
  extend the `History` collapse special-case from `events` to also cover
  `items`.

## Tests

- Valid fixtures: `Maybe` at the start / middle / end of the history, nested
  `Maybe`, empty `Maybe`, blocks in any order, single-line blocks.
- Invalid fixtures: the v1 invalid cases re-expressed with a `Maybe` present,
  plus `Maybe`-specific syntax errors, a duplicate event name across a `Maybe`
  boundary, undeclared names inside a `Maybe`, and a `Recv` of a later send
  inside a `Maybe`.
- Run with `pytest -q` inside the worktree's `.venv` (or after
  `pip install --editable . --group dev`).

## Next phase (deliberately not now)

1. Walk the `RefinedAst` by hand and build the CFG manually: `entry` / `exit`
   nodes, one node per event, and a `fork` / `join` pair per `Maybe` with
   *enter* and *skip* edges. Render it as DOT to see the graph.
2. Define the static checks over that graph (dominance-based causality,
   recipient membership, and later the `Rules` block sketched in
   `example.st`), collecting all diagnostics instead of stopping at the
   first.
3. Only after the manual walk is understood, codify it as `cfg.py` /
   `checks.py` in `spacetime/v2/`.

## Open decisions

- `Maybe` is unnamed (simplicity bias); an optional label can be added later
  for diagnostics.
- The `Rules { ack <- request }` block sketched in `example.st` is deferred
  to the checks phase.
