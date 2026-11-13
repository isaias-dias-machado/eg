# Plan: "to svg" backend

Implements `docs/svg_target.md`. Renders a `RefinedAst` (output of
`spacetime.compiler.compile_source`) as one self-contained SVG file: a
Lamport space-time diagram with horizontal lifelines, time flowing left
to right. Golden example: `docs/sample_v2.svg` from `example.txt`.

## Locked decisions

- **Dashed arrows are lost messages.** For a recipient that never receives
  a send, draw a vertical dashed arrow (`stroke-dasharray="4 3"`) from the
  send dot straight to the *intended* recipient's lifeline at the send's
  x. Arrowhead at the lifeline, **no dot**.
- **The golden file wins numeric disputes.** The spec table says arrows end
  5 px short of a lifeline, but `sample_v2.svg` ends the dashed arrow at
  y=272 (8 px short of r's lifeline at 280). We match the golden (8 px for
  the dashed end) and annotate the spec table.
- **Solid-arrow endpoints use facing offsets** (start = `ys + 5·sign(yr−ys)`,
  end = `yr − 5·sign(yr−ys)`), the only rule consistent with the golden's
  m1/m2 arrows. The golden's m3 start (245, 285) contradicted its own m2
  arrow, so `sample_v2.svg` and the spec worked example were corrected to
  (245, 275) → (280, 185).
- **Label text is the payload** (`SendEventRefined.message`), per spec.
  The golden abbreviates payloads to message names, so the golden test
  masks `<text>` label elements (text and x position — the golden's label
  x values are hand-tuned, not formula-derived); a separate unit test
  pins label text == payload and the label position formula.
- **CLI**: `spacetime FILE --to-svg` prints the SVG to stdout (redirect to
  write the file). Default behavior (print refined AST) unchanged.

## Work items

1. `spacetime/semantics.py` — `message_type` becomes the message's 0-based
   declaration index in the `Messages` block (currently hardcoded `1`).
   Build `message_index = {decl.name.name: i for i, decl in
   enumerate(ast.message_declarations)}`; delete the unused
   `messages_seen` / `messages_seen_count` bookkeeping.
2. `spacetime/svg.py` (new) — `render_svg(program: RefinedAst) -> str`.
   Pure function, no I/O. Layout pass then emission pass (below).
3. `spacetime/__init__.py` — re-export `render_svg`.
4. `spacetime/cli.py` — add `--to-svg` flag; on success print
   `render_svg(program)` instead of the text rendering.
5. `tests/test_svg.py` (new) — golden test + invariant tests + edge cases.
6. `docs/svg_target.md` — annotate the dashed-end offset (8 px, per
   golden) and the label-abbreviation note.

## Layout algorithm

Constants: `X_START=48`, `X0=70`, `STEP=35`, `Y0=80`, `DY=100`, dot
`r=3`, arrow offset `5`, `X_END = max(300, x_last_dot + 20)`,
`W = X_END + 60`, `H = Y0 + (n-1)*DY + 40`, `viewBox="0 0 W H"`.

1. **Dots.** Walk `history.events` in `temporal_pos` order. Each send
   contributes one dot at `process_from_id`; each recv one dot per entry
   of `process_ids` (listed order). Assign `x_k = X0 + k*STEP`,
   `y = Y0 + process_index * DY`. Keep a map `(send_event, process) ->
   dot` so arrows can find recv dots. Invariants: all x distinct, every
   consecutive pair exactly `STEP` apart.
2. **Lifelines.** One `<line>` per process, declaration order top to
   bottom: `(X_START, y_i)` to `(X_END, y_i)`, `stroke="#555"`,
   `stroke-width="1.5"`, `marker-end="url(#t)"`. Label at `(40, y_i+4)`,
   `text-anchor="end"`, bold, `font-size="13"`.
3. **Arrows.** Per send, per recipient in `processes_to_ids` order.
   Color = `PALETTE[message_type % 3]` (`0:#5b7fa6`, `1:#6f9a76`,
   `2:#b0765a`), marker `url(#a{type+1})`.
   - recipient == sender (self-send): cubic Bézier
     `M xs+3 y+6 C xs+7 y+38, x_recv-4 y+38, x_recv y+6`, where
     `(x_recv, y)` is the sender's recv dot for this send.
   - recipient has a recv dot for this send: solid line from send dot to
     recv dot. With `d = sign(y_recv - y_send)`: start `(xs, ys + 5d)`,
     end `(xr, yr - 5d)`.
   - recipient never receives (lost): vertical dashed line from
     `(xs, ys + 5d)` to `(xs, y_recipient - 8d)` — 8 px short per the
     golden — no dot.
4. **Labels.** One per send: midpoint of the arrow to the first recipient
   that *receives* it, offset `(+7, +4)`, `text-anchor="start"`,
   `font-size="11"`, italic, fill = message color, text = payload
   (XML-escaped).

## Emission format

Tab-indented, element order: `<defs>` (gray marker `t` `markerWidth="8"`
plus one `a{i}` per palette color `markerWidth="7"`; all
`viewBox="0 0 10 10" refX="9" refY="5" orient="auto"`, path
`M0 0 L10 5 L0 10 z`), lifelines, process labels, arrows with labels,
dots last (on top). Root: `viewBox`, `xmlns="http://www.w3.org/2000/svg"`,
`font-family="Helvetica, Arial, sans-serif"`. Escape all text content
(`&`, `<`, `>`, quotes in attributes).

## Tests (`tests/test_svg.py`)

- **Golden**: compile `example.txt`, render, compare to
  `docs/sample_v2.svg` with label `<text>` elements masked; everything
  else byte-exact.
- **Invariants** (parse with `xml.etree.ElementTree`): one horizontal
  lifeline per process in declaration order; dot x's are exactly
  `X0 + k*STEP` and all distinct, `r="3" fill="#555"`; every `url(#...)`
  resolves to a defined marker; all coordinates inside the viewBox; one
  muted color per `message_type` shared by arrow, marker and label;
  self-send -> `<path>` loop; lost recipient -> dashed vertical `<line>`
  with no dot at the target.
- **Unit**: label text == payload; label position == arrow midpoint +
  (7, 4); `message_type` == declaration index (semantics change).
- **Edge cases**: empty history (`X_END=300`), single process, multicast,
  self-send only, all-lost multicast.

## Open questions

- Self-send that is never received: no recv dot exists for the loop.
  Proposed default: treat as lost — short dashed vertical stub below the
  send dot, no dot. Needs confirmation.
- Duplicate recipient in `processes_to_ids`: draw one arrow per listing
  (spec-literal) or dedupe preserving order (proposed).

## Git workflow

`master` currently has untracked files (`docs/svg_target.md`,
`docs/sample_v2.svg`, `example.st`, plus this plan). Before editing:
commit those on `master`, then create worktree `agent/svg-backend` and
implement there; never commit to `master` directly; leave the tree clean
at the end of the task.
