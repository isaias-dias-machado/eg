"""SVG rendering of a refined AST as a Lamport space-time diagram.

The diagram has horizontal lifelines (time flows left to right), one per
process in declaration order. Events become dots spaced ``STEP`` apart
across all lifelines, sends connect to their receives with colored
arrows, and a recipient that never receives a send gets a vertical
dashed arrow (a lost message) pointing at its lifeline, with no dot.
Arrows carry no inline labels; a caption legend below the diagram decodes
each color to its message name. See ``docs/svg_target.md`` for the full
specification and ``docs/sample_v2.svg`` for the golden example.

The only public entry point is :func:`render_svg`.
"""

from dataclasses import dataclass
from xml.sax.saxutils import escape

from .ast import RecvEventRefined, RefinedAst, SendEventRefined

# Layout constants (docs/svg_target.md).
X_START = 48
X0 = 70
STEP = 35
Y0 = 80
DY = 100
DOT_RADIUS = 3
ARROW_OFFSET = 5
# Dashed (lost) arrows end 8 px short of the target lifeline, matching the
# golden sample_v2.svg (the spec table's "5 px" applies to solid arrows).
LOST_OFFSET = 8
# Self-loop shape: start/end offsets from the send dot and control depth.
SELF_LOOP_START_DX = 3
SELF_LOOP_START_DY = 6
SELF_LOOP_CTRL1_DX = 7
SELF_LOOP_CTRL2_DX = -4
SELF_LOOP_DEPTH = 38
# A self-send that is never received is drawn as a short dashed stub below
# the send dot (there is no recv dot to loop to).
SELF_LOOP_STUB = 30
LIFELINE_COLOR = "#555"
PALETTE = ("#5b7fa6", "#6f9a76", "#b0765a")
# Caption legend below the diagram: one entry per used message type, in
# ascending palette order. The swatch resembles the arrow line; the text is
# neutral gray and carries the message name.
CAPTION_SWATCH_X = 48
CAPTION_TEXT_X = 78
CAPTION_SWATCH_WIDTH = 24
CAPTION_SWATCH_HEIGHT = 3
# Swatch y relative to the entry's text baseline: centers the 3 px bar on
# the x-height of the 11 px caption text.
CAPTION_SWATCH_DY = -7
CAPTION_LINE_HEIGHT = 18
# Gap from the last lifeline to the first caption line; clears the self-loop
# bulge (loops reach SELF_LOOP_DEPTH = 38 px below a lifeline).
CAPTION_TOP_GAP = 60
CAPTION_BOTTOM_GAP = 20
CAPTION_TEXT_COLOR = "#555"


@dataclass(frozen=True)
class _Dot:
    """One event dot on a lifeline.

    Invariants:
        - ``x`` is ``X0 + k*STEP`` for the dot's global index ``k``, so all
          dot x-coordinates are distinct and evenly spaced.
        - ``y`` is the lifeline y of ``process``.
    """

    x: int
    y: int
    process: str


@dataclass(frozen=True)
class _Layout:
    """Geometry of one diagram.

    Invariants:
        - ``dots`` is ordered by temporal position; ``send_dots`` maps a
          send's ``temporal_pos`` to its dot; ``recv_dots`` maps
          ``(send temporal_pos, process)`` to that process's recv dot.
        - ``caption_entries`` lists ``(message_type, message_name)`` per
          used message type in ascending palette order, and ``caption_y0``
          is the first entry's text baseline (``None`` when no send exists,
          in which case there is no caption).
        - ``width``/``height`` follow the viewBox formula in the spec.
    """

    processes: list[str]
    y_of: dict[str, int]
    dots: list[_Dot]
    send_dots: dict[int, _Dot]
    recv_dots: dict[tuple[int, str], _Dot]
    x_end: int
    width: int
    height: int
    caption_entries: list[tuple[int, str]]
    caption_y0: int | None


def _layout(program: RefinedAst) -> _Layout:
    """Compute dot positions and canvas size for ``program``.

    Failure modes:
        Raises ``KeyError`` if an event names a process missing from
        ``process_declarations`` and ``TypeError`` for a foreign event
        node; neither can happen for a ``RefinedAst`` produced by
        :func:`spacetime.compiler.compile_source`.
    """
    y_of = {
        name: Y0 + index * DY
        for index, name in enumerate(program.process_declarations)
    }
    dots: list[_Dot] = []
    send_dots: dict[int, _Dot] = {}
    recv_dots: dict[tuple[int, str], _Dot] = {}

    events = sorted(program.history.events, key=lambda event: event.temporal_pos)
    for event in events:
        if isinstance(event, SendEventRefined):
            dot = _Dot(
                x=X0 + len(dots) * STEP,
                y=y_of[event.process_from_id],
                process=event.process_from_id,
            )
            dots.append(dot)
            send_dots[event.temporal_pos] = dot
        elif isinstance(event, RecvEventRefined):
            for process in event.process_ids:
                dot = _Dot(
                    x=X0 + len(dots) * STEP,
                    y=y_of[process],
                    process=process,
                )
                dots.append(dot)
                recv_dots[(event.related_send_event.temporal_pos, process)] = dot
        else:
            raise TypeError(f"unexpected event: {event!r}")

    x_last = dots[-1].x if dots else X0
    x_end = max(300, x_last + 20)
    process_count = len(program.process_declarations)
    last_y = Y0 + (process_count - 1) * DY

    # One caption entry per used message type, keeping the first message
    # name seen for each type; ordered by palette index, then type.
    used_types: dict[int, str] = {}
    for event in events:
        if isinstance(event, SendEventRefined) and event.message_type not in used_types:
            used_types[event.message_type] = event.message_name
    caption_entries = sorted(
        used_types.items(), key=lambda item: (item[0] % len(PALETTE), item[0])
    )
    if caption_entries:
        caption_y0 = last_y + CAPTION_TOP_GAP
        height = (
            caption_y0
            + (len(caption_entries) - 1) * CAPTION_LINE_HEIGHT
            + CAPTION_BOTTOM_GAP
        )
    else:
        caption_y0 = None
        height = last_y + 40

    return _Layout(
        processes=program.process_declarations,
        y_of=y_of,
        dots=dots,
        send_dots=send_dots,
        recv_dots=recv_dots,
        x_end=x_end,
        width=x_end + 60,
        height=height,
        caption_entries=caption_entries,
        caption_y0=caption_y0,
    )


def _marker(marker_id: str, color: str, width: int, *, depth: int) -> str:
    """One arrowhead ``<marker>`` definition at the given tab depth."""
    indent = "\t" * depth
    return (
        f'{indent}<marker id="{marker_id}" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="{width}" markerHeight="{width}" orient="auto">\n'
        f'{indent}\t<path d="M0 0 L10 5 L0 10 z" fill="{color}"/>\n'
        f"{indent}</marker>"
    )


def _dashed_line(
    start: tuple[int, int],
    end: tuple[int, int],
    color: str,
    marker: str,
) -> str:
    """A dashed arrow line (lost message) from ``start`` to ``end``."""
    return (
        f'\t<line x1="{start[0]}" y1="{start[1]}" x2="{end[0]}" y2="{end[1]}" '
        f'stroke="{color}" stroke-width="1.5" stroke-dasharray="4 3" '
        f'marker-end="url(#{marker})"/>'
    )


def _arrow_elements(layout: _Layout, send: SendEventRefined) -> list[str]:
    """SVG elements for one send: one arrow per recipient, no inline label.

    Invariants:
        - recipients are drawn in ``processes_to_ids`` order, duplicates
          removed;
        - arrows stay colored; the caption legend emitted by
          :func:`render_svg` decodes the color to the message name.
    """
    palette_index = send.message_type % len(PALETTE)
    color = PALETTE[palette_index]
    marker = f"a{palette_index + 1}"
    send_dot = layout.send_dots[send.temporal_pos]
    elements: list[str] = []

    for recipient in dict.fromkeys(send.processes_to_ids):
        y_recipient = layout.y_of[recipient]
        direction = 1 if y_recipient > send_dot.y else -1
        recv = layout.recv_dots.get((send.temporal_pos, recipient))

        if recipient == send.process_from_id and recv is not None:
            # Self-send: loop below the lifeline to the sender's recv dot.
            path = (
                f"M {send_dot.x + SELF_LOOP_START_DX} {send_dot.y + SELF_LOOP_START_DY} "
                f"C {send_dot.x + SELF_LOOP_CTRL1_DX} {send_dot.y + SELF_LOOP_DEPTH}, "
                f"{recv.x + SELF_LOOP_CTRL2_DX} {recv.y + SELF_LOOP_DEPTH}, "
                f"{recv.x} {recv.y + SELF_LOOP_START_DY}"
            )
            elements.append(
                f'\t<path d="{path}" fill="none" stroke="{color}" '
                f'stroke-width="1.5" marker-end="url(#{marker})"/>'
            )
        elif recv is not None:
            # Solid arrow from the send dot to the recv dot, both endpoints
            # offset ARROW_OFFSET away from their lifelines.
            start = (send_dot.x, send_dot.y + ARROW_OFFSET * direction)
            end = (recv.x, recv.y - ARROW_OFFSET * direction)
            elements.append(
                f'\t<line x1="{start[0]}" y1="{start[1]}" x2="{end[0]}" y2="{end[1]}" '
                f'stroke="{color}" stroke-width="1.5" marker-end="url(#{marker})"/>'
            )
        elif recipient == send.process_from_id:
            # Self-send never received: short dashed stub below the send dot.
            start = (send_dot.x, send_dot.y + ARROW_OFFSET)
            end = (send_dot.x, send_dot.y + ARROW_OFFSET + SELF_LOOP_STUB)
            elements.append(_dashed_line(start, end, color, marker))
        else:
            # Lost message: vertical dashed arrow to the intended recipient's
            # lifeline at the send's x, no dot.
            start = (send_dot.x, send_dot.y + ARROW_OFFSET * direction)
            end = (send_dot.x, y_recipient - LOST_OFFSET * direction)
            elements.append(_dashed_line(start, end, color, marker))

    return elements


def _caption_elements(layout: _Layout) -> list[str]:
    """The caption legend: one swatch + message-name line per used type.

    Invariants:
        - entries follow ``layout.caption_entries`` (ascending palette
          order); the swatch ``fill`` is the message color and the text is
          neutral ``#555`` carrying the message name;
        - entry ``i`` has its text baseline at ``caption_y0 + i*18`` and its
          swatch at ``text_y - 7``, so the 3 px bar sits on the text's
          x-height;
        - returns an empty list when the history has no sends.
    """
    if not layout.caption_entries:
        return []
    lines = ['\t<g id="caption">']
    for index, (message_type, message_name) in enumerate(layout.caption_entries):
        color = PALETTE[message_type % len(PALETTE)]
        text_y = layout.caption_y0 + index * CAPTION_LINE_HEIGHT
        lines.append(
            f'\t\t<rect x="{CAPTION_SWATCH_X}" y="{text_y + CAPTION_SWATCH_DY}" '
            f'width="{CAPTION_SWATCH_WIDTH}" height="{CAPTION_SWATCH_HEIGHT}" '
            f'fill="{color}"/>'
        )
        lines.append(
            f'\t\t<text x="{CAPTION_TEXT_X}" y="{text_y}" font-size="11" '
            f'fill="{CAPTION_TEXT_COLOR}">{escape(message_name)}</text>'
        )
    lines.append("\t</g>")
    return lines


def render_svg(program: RefinedAst) -> str:
    """Render ``program`` as one self-contained SVG string.

    Purpose: produce the Lamport space-time diagram specified in
    ``docs/svg_target.md`` (horizontal lifelines, time left to right).

    Invariants of the output:
        - element order: ``<defs>`` markers, lifelines, process labels,
          arrows, dots, caption last (``<g id="caption">``);
        - dot x-coordinates are ``X0 + k*STEP`` and all distinct;
        - every ``url(#...)`` reference resolves to a marker in ``<defs>``;
        - the string ends with a newline.

    Failure modes:
        Raises ``KeyError`` or ``TypeError`` only if ``program`` was not
        produced by the compiler (undeclared process, foreign event node).
    """
    layout = _layout(program)
    lines = [
        f'<svg viewBox="0 0 {layout.width} {layout.height}" '
        'xmlns="http://www.w3.org/2000/svg" font-family="Helvetica, Arial, sans-serif">'
    ]

    lines.append("\t<defs>")
    lines.append(_marker("t", LIFELINE_COLOR, 8, depth=2))
    events = sorted(program.history.events, key=lambda event: event.temporal_pos)
    used_palette = sorted(
        {
            event.message_type % len(PALETTE)
            for event in events
            if isinstance(event, SendEventRefined)
        }
    )
    for palette_index in used_palette:
        lines.append(_marker(f"a{palette_index + 1}", PALETTE[palette_index], 7, depth=2))
    lines.append("\t</defs>")

    for name in layout.processes:
        y = layout.y_of[name]
        lines.append(
            f'\t<line x1="{X_START}" y1="{y}" x2="{layout.x_end}" y2="{y}" '
            f'stroke="{LIFELINE_COLOR}" stroke-width="1.5" marker-end="url(#t)"/>'
        )

    for name in layout.processes:
        y = layout.y_of[name]
        lines.append(
            f'\t<text x="40" y="{y + 4}" text-anchor="end" font-size="13" '
            f'font-weight="bold">{escape(name)}</text>'
        )

    for event in events:
        if isinstance(event, SendEventRefined):
            lines.extend(_arrow_elements(layout, event))

    for dot in layout.dots:
        lines.append(
            f'\t<circle cx="{dot.x}" cy="{dot.y}" r="{DOT_RADIUS}" fill="{LIFELINE_COLOR}"/>'
        )

    lines.extend(_caption_elements(layout))

    lines.append("</svg>")
    return "\n".join(lines) + "\n"
