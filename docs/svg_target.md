# SVG rendering target

Specification for the diagram the compiler emits: a Lamport space-time
diagram with **horizontal lifelines** (time flows left to right), as one
self-contained SVG file per program. The golden example is
[`sample_v2.svg`](sample_v2.svg), which corresponds to [`../example.txt`](../example.txt).

## Input

The renderer consumes a `RefinedAst` (output of
`spacetime.compiler.compile_source`):

- `process_declarations: list[str]` — process names in declaration order;
- `history.events` — `SendEventRefined` / `RecvEventRefined`, ordered by
  `temporal_pos`:
  - **send**: `message` (payload string), `message_type` (int),
    `process_from_id`, `processes_to_ids` (multicast = several recipients);
  - **recv**: `related_send_event`, `process_ids` (a subset of the send's
    recipients; one dot per process).

## Layout constants

| constant | value | meaning |
|---|---|---|
| `X_START` | 48 | left end of every lifeline |
| `X_END` | `max(300, x_last_dot + 20)` | right end of every lifeline (arrowhead) |
| `X0` | 70 | x of the first dot |
| `STEP` | 35 | constant gap between consecutive dots |
| `Y0` | 80 | y of the first (topmost) lifeline |
| `DY` | 100 | vertical gap between lifelines |
| dot radius | 3 | |
| arrow offset | 5 | arrows start/end 5 px short of a lifeline |
| viewBox | `0 0 W H` with `W = X_END + 60`, `H = Y0 + (n-1)*DY + 40` | `n` = number of processes |

For 3 processes and 7 dots this gives `0 0 360 320`, exactly as in
`sample_v2.svg`.

## Lifelines

One horizontal `<line>` per process, in declaration order from top to
bottom: `y_i = Y0 + i*DY`, from `(X_START, y_i)` to `(X_END, y_i)`, stroke
`#555`, `stroke-width="1.5"`, with a gray arrowhead marker at the right end
(time direction). The process label sits at `(40, y_i + 4)` with
`text-anchor="end"`, bold, `font-size="13"`.

## Event dots

Flatten the history into dots, in this order:

1. each send event contributes **one** dot at its `process_from_id`;
2. each recv event contributes **one dot per process** in `process_ids`,
   in listed order.

Sort all dots by `temporal_pos` (within one event, by the order above) and
assign `x_k = X0 + k*STEP`; the y is the process's lifeline. This enforces
two invariants:

- **even spacing** — every consecutive pair of dots, across *all*
  lifelines, is exactly `STEP` apart;
- **no vertical alignment** — all dot x-coordinates are distinct, so no
  two events are ever drawn as parallel.

Dots are `<circle r="3" fill="#555">` — always the lifeline color, never a
message color — and are emitted last, on top of everything else.

## Message arrows

For each send event, for each recipient in `processes_to_ids` (in order):

| case | drawing |
|---|---|
| recipient == sender (self-send) | self-loop: cubic Bézier from `(x_send + 3, y + 6)` to `(x_recv, y + 6)` with control points `(x_send + 7, y + 38)` and `(x_recv - 4, y + 38)`, bulging below the lifeline; `x_recv` is the sender's recv dot for this send |
| recipient has a recv dot for this send | solid arrow from the send dot to that recv dot |
| recipient never receives this send | dashed arrow (`stroke-dasharray="4 3"`) from the send dot straight to the recipient's lifeline at the send's x; arrowhead at the lifeline, **no dot** |

Arrow endpoints are offset 5 px from the lifelines (perpendicular) so the
arrowhead does not overlap the line or the dot.

### Color per message type

`message_type` indexes a muted palette, cyclically:

| index | color | example message |
|---|---|---|
| 0 | `#5b7fa6` steel blue | `request` |
| 1 | `#6f9a76` sage green | `ack` |
| 2 | `#b0765a` clay | `vote` |

All arrows of the same message type — solid, self-loop and dashed — share
one color, and each palette color gets its own arrowhead `<marker>` with a
matching fill. Colors must stay muted (desaturated); no bright primaries.

(Note: `spacetime/semantics.py` currently hardcodes `message_type = 1`;
it should become the message's 0-based declaration index in the
`Messages` block.)

### Labels

One label per send event, placed at the midpoint of the arrow to the first
recipient that receives it, offset by about `(+7, +4)`, `text-anchor`
start, `font-size="11"`, italic, fill = the message color. The text is the
payload `SendEventRefined.message` (`sample_v2.svg` abbreviates the
payloads to the message names `request` / `ack` for compactness).

## File structure

Element order: `<defs>` (markers), lifelines, process labels, arrows with
labels, dots. Tab-indented, single self-contained file, root carries
`font-family="Helvetica, Arial, sans-serif"`. Markers: one gray lifeline
marker (`markerWidth="8"`) plus one per palette color (`markerWidth="7"`),
all with `viewBox="0 0 10 10" refX="9" refY="5" orient="auto"` and path
`M0 0 L10 5 L0 10 z`.

## Worked example: `example.txt` → `sample_v2.svg`

Dots (x = 70 + 35k):

| k | event | process | dot |
|---|---|---|---|
| 0 | `m1` send | p | (70, 80) |
| 1 | `Recv(m1)` | q | (105, 180) |
| 2 | `m2` send | q | (140, 180) |
| 3 | `Recv(m2)` | p | (175, 80) |
| 4 | `Recv(m2)` | q | (210, 180) |
| 5 | `m3` send | r | (245, 280) |
| 6 | `Recv(m3)` | q | (280, 180) |

Arrows:

- `m1` (request, blue): (70, 85) → (105, 175), label `request` at (96, 134);
- `m2` (ack, green): (140, 175) → (175, 85), label `ack` at (165, 134);
  self-loop `M 143 186 C 147 218, 206 218, 210 186`; dashed (140, 185) →
  (140, 272) toward r, which never receives `m2`;
- `m3` (request, blue): (245, 285) → (280, 185), label `request` at (269, 239).

## Invariants (checklist for tests)

- lifelines are horizontal, one per process, in declaration order;
- dots: `r="3"`, `fill="#555"`, x = `X0 + k*STEP` — evenly spaced and all
  distinct;
- one muted color per message type, shared by arrow, marker and label;
- self-send → loop; unreceived recipient → dashed arrow with no dot;
- output is valid standalone SVG: parseable XML, every `url(#...)`
  reference resolves, all coordinates inside the viewBox.

A golden test can compile `example.txt`, render it, and compare against
`docs/sample_v2.svg`.
