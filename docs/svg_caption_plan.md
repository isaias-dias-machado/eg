# Plan: caption legend for the SVG backend

Follow-up to `docs/svg_backend_plan.md` (implemented on `agent/svg-backend`).
Problem: the per-arrow italic message labels can overlap arrows and each
other. Solution: remove inline labels entirely (no flag — the caption is
the default and only message text) and put the color → message-type
mapping in a **caption**: a column of entries below the diagram, one per
line.

## Locked decisions

- **No inline labels, no flag.** The label block in `_arrow_elements` is
  removed. Arrows stay colored; the caption decodes them.
- **Column format.** One caption entry per line below the diagram. The
  canvas width never grows because of the caption: `W = X_END + 60` as
  before (no horizontal row, no overflow handling).
- **Swatch.** Each entry starts with a slim `<rect>` — 24 × 3 px,
  `fill` = the message color — at `x = 48`, resembling the arrow line.
- **Neutral text.** The caption text sits at `x = 78`, `font-size="11"`,
  `fill="#555"` (neutral, not the message color). Text = the message
  **name** (`request`, `ack`), which requires adding `message_name` back
  to `SendEventRefined` (`RefinedAst` currently keeps only the payload).
- **Geometry.** `caption_y0 = Y0 + (n-1)*DY + 60` — the +60 clears the
  self-loop bulge (loops reach 38 px below a lifeline). Line height 18 px.
  With `k` used message types: entries at `y = caption_y0 + i*18`,
  `H = caption_y0 + (k-1)*18 + 20`. With no used types (empty history):
  no caption, `H = Y0 + (n-1)*DY + 40` as before.
- **Element order.** defs, lifelines, process labels, arrows, dots,
  caption last, wrapped in `<g id="caption">`.
- **Golden.** `docs/sample_v2.svg` is regenerated: the 3 inline labels
  are removed, the 2-line caption is added. The golden test becomes
  byte-exact — no more masking of label elements.

For `example.st` (processes p, q, r; types request=0, ack=1):
`viewBox="0 0 360 378"`, caption lines at y=340 (`request`, blue swatch)
and y=358 (`ack`, green swatch).

## Work items

1. `spacetime/ast.py` + `spacetime/semantics.py` — add
   `message_name: str` to `SendEventRefined`, populated from the
   `Messages` declaration.
2. `spacetime/svg.py` — remove the label block from `_arrow_elements`;
   add caption emission; adjust `H`.
3. `docs/sample_v2.svg` — regenerate (remove inline labels, add caption).
4. `docs/svg_target.md` — replace the "Labels" section with a "Caption"
   section describing the column format, swatch, neutral text, geometry.
5. `tests/test_svg.py` — caption invariants: one line per used message
   type in ascending palette order; swatch `fill` = palette color; text
   `fill="#555"` and text = message name; caption y below every dot and
   loop; all coordinates inside the viewBox; no italic inline labels
   remain. Update the tests that currently assert inline labels; golden
   test drops the masking.
6. Git: new worktree `agent/svg-caption` based on `agent/svg-backend`;
   implement and commit there; never commit to `master`; leave the tree
   clean.

## Validation

- `python -m pytest tests/test_svg.py -v` from the worktree (16+ tests).
- `python -m spacetime --to-svg example.st > /tmp/out.svg` and
  `diff /tmp/out.svg docs/sample_v2.svg` — must be empty (byte-exact).
- Parse `/tmp/out.svg` with `xml.etree.ElementTree` and open it in a
  browser to eyeball the caption.
