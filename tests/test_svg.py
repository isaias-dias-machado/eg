"""Tests for the SVG backend (:func:`spacetime.svg.render_svg`).

Covers the golden example (``example.st`` vs ``docs/sample_v2.svg``,
byte-exact), the layout invariants from ``docs/svg_target.md``, the
caption legend, the ``message_type``/``message_name`` semantics, edge
cases, and the ``--to-svg`` CLI flag.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

from spacetime import SendEventRefined, compile_file, compile_source, render_svg
from spacetime.cli import main

ROOT = Path(__file__).parents[1]
NS = "{http://www.w3.org/2000/svg}"


def _parse(svg_text: str) -> ET.Element:
    """Parse SVG text, failing the test on malformed XML."""
    return ET.fromstring(svg_text)


def _elements(root: ET.Element, tag: str) -> list[ET.Element]:
    return root.findall(f".//{NS}{tag}")


def _caption(root: ET.Element) -> ET.Element | None:
    """The ``<g id="caption">`` element, or ``None`` when absent."""
    return root.find(f".//{NS}g[@id='caption']")


def test_golden_example_matches_sample_v2_byte_exact() -> None:
    program = compile_file(ROOT / "example.st")
    rendered = render_svg(program)
    golden = (ROOT / "docs" / "sample_v2.svg").read_text()

    assert rendered == golden


def test_no_inline_message_labels_remain() -> None:
    root = _parse(render_svg(compile_file(ROOT / "example.st")))

    italic = [
        element
        for element in _elements(root, "text")
        if element.attrib.get("font-style") == "italic"
    ]
    assert italic == []


def test_caption_decodes_used_message_types_in_palette_order() -> None:
    root = _parse(render_svg(compile_file(ROOT / "example.st")))

    caption = _caption(root)
    assert caption is not None
    entries = list(caption)
    assert len(entries) == 4  # two swatch + text pairs

    swatches = [e for e in entries if e.tag == NS + "rect"]
    texts = [e for e in entries if e.tag == NS + "text"]
    assert [s.attrib["fill"] for s in swatches] == ["#5b7fa6", "#6f9a76"]
    assert [t.text for t in texts] == ["request", "ack"]
    for swatch in swatches:
        assert swatch.attrib["x"] == "48"
        assert swatch.attrib["width"] == "24"
        assert swatch.attrib["height"] == "3"
    for text in texts:
        assert text.attrib["x"] == "78"
        assert text.attrib["font-size"] == "11"
        assert text.attrib["fill"] == "#555"
    # Entry lines at y = 340 and y = 358; swatches sit at text_y - 7.
    assert [t.attrib["y"] for t in texts] == ["340", "358"]
    assert [s.attrib["y"] for s in swatches] == ["333", "351"]


def test_caption_sits_below_every_dot_and_loop() -> None:
    root = _parse(render_svg(compile_file(ROOT / "example.st")))

    caption = _caption(root)
    assert caption is not None
    caption_ys = [int(e.attrib["y"]) for e in caption if e.tag == NS + "text"]
    max_dot_y = max(int(c.attrib["cy"]) for c in _elements(root, "circle"))
    # Self-loops bulge 38 px below their lifeline.
    assert min(caption_ys) > max_dot_y + 38


def test_caption_absent_when_history_has_no_sends() -> None:
    program = compile_source("Processes {\n  p\n  q\n}\n")
    root = _parse(render_svg(program))

    assert _caption(root) is None
    assert root.attrib["viewBox"] == "0 0 360 220"


def test_lifelines_are_horizontal_and_in_declaration_order() -> None:
    root = _parse(render_svg(compile_file(ROOT / "example.st")))

    assert root.attrib["viewBox"] == "0 0 360 378"
    lifelines = [
        element
        for element in _elements(root, "line")
        if element.attrib.get("marker-end") == "url(#t)"
    ]
    assert [(e.attrib["x1"], e.attrib["y1"], e.attrib["x2"], e.attrib["y2"]) for e in lifelines] == [
        ("48", "80", "300", "80"),
        ("48", "180", "300", "180"),
        ("48", "280", "300", "280"),
    ]
    for lifeline in lifelines:
        assert lifeline.attrib["y1"] == lifeline.attrib["y2"]
        assert lifeline.attrib["stroke"] == "#555"

    process_labels = [
        element
        for element in _elements(root, "text")
        if element.attrib.get("font-weight") == "bold"
    ]
    assert [element.text for element in process_labels] == ["p", "q", "r"]
    assert [element.attrib["y"] for element in process_labels] == ["84", "184", "284"]


def test_dots_are_evenly_spaced_distinct_and_on_lifelines() -> None:
    root = _parse(render_svg(compile_file(ROOT / "example.st")))

    circles = _elements(root, "circle")
    assert len(circles) == 7
    xs = [int(circle.attrib["cx"]) for circle in circles]
    assert xs == [70 + 35 * k for k in range(7)]
    assert len(set(xs)) == len(xs)
    for circle in circles:
        assert circle.attrib["r"] == "3"
        assert circle.attrib["fill"] == "#555"
        assert int(circle.attrib["cy"]) in {80, 180, 280}


def test_every_marker_reference_resolves_and_coordinates_are_inside_viewbox() -> None:
    root = _parse(render_svg(compile_file(ROOT / "example.st")))

    marker_ids = {marker.attrib["id"] for marker in _elements(root, "marker")}
    assert marker_ids == {"t", "a1", "a2"}
    width, height = (int(value) for value in root.attrib["viewBox"].split()[2:])
    for element in root.iter():
        reference = element.attrib.get("marker-end", "")
        if reference.startswith("url(#"):
            assert reference[5:-1] in marker_ids
        for attribute in ("x1", "y1", "x2", "y2", "cx", "cy", "x", "y"):
            if attribute in element.attrib:
                value = int(element.attrib[attribute])
                assert 0 <= value <= (width if attribute in {"x1", "x2", "cx", "x"} else height)


def test_arrow_kinds_and_colors_for_example() -> None:
    root = _parse(render_svg(compile_file(ROOT / "example.st")))

    lines = _elements(root, "line")
    solid = [e for e in lines if "stroke-dasharray" not in e.attrib and e.attrib.get("marker-end") != "url(#t)"]
    dashed = [e for e in lines if "stroke-dasharray" in e.attrib]

    # m1 and m3 are request (type 0, steel blue); m2 is ack (type 1, sage).
    assert [(e.attrib["x1"], e.attrib["y1"], e.attrib["x2"], e.attrib["y2"], e.attrib["stroke"]) for e in solid] == [
        ("70", "85", "105", "175", "#5b7fa6"),
        ("140", "175", "175", "85", "#6f9a76"),
        ("245", "275", "280", "185", "#5b7fa6"),
    ]

    # m2 is lost for r: vertical dashed arrow to r's lifeline, no dot there.
    assert len(dashed) == 1
    lost = dashed[0]
    assert lost.attrib["x1"] == lost.attrib["x2"] == "140"
    assert lost.attrib["y1"] == "185"
    assert lost.attrib["y2"] == "272"
    assert lost.attrib["stroke-dasharray"] == "4 3"
    assert lost.attrib["stroke"] == "#6f9a76"
    assert not any(
        circle.attrib["cx"] == "140" and circle.attrib["cy"] == "280"
        for circle in _elements(root, "circle")
    )

    # Self-send m2 -> q is a cubic loop below q's lifeline.
    paths = _elements(root, "path")
    loop = [p for p in paths if p.attrib.get("fill") == "none"]
    assert len(loop) == 1
    assert loop[0].attrib["d"] == "M 143 186 C 147 218, 206 218, 210 186"
    assert loop[0].attrib["stroke"] == "#6f9a76"

    # One marker per used palette color, fill matching the arrow color.
    markers = {m.attrib["id"]: m for m in _elements(root, "marker")}
    assert markers["t"].attrib["markerWidth"] == "8"
    assert markers["a1"].attrib["markerWidth"] == "7"
    assert markers["a1"].find(f"{NS}path").attrib["fill"] == "#5b7fa6"
    assert markers["a2"].find(f"{NS}path").attrib["fill"] == "#6f9a76"


def test_message_type_is_declaration_index() -> None:
    program = compile_source(
        """Processes {
  p
  q
}

Messages {
  request := "r"
  ack := "a"
  vote := "v"
}

History {
  m1 := Send(vote) :: p -> q
  Recv(m1) :: q
  m2 := Send(request) :: p -> q
  Recv(m2) :: q
}
"""
    )
    sends = [e for e in program.history.events if isinstance(e, SendEventRefined)]
    assert [send.message_type for send in sends] == [2, 0]
    assert [send.message_name for send in sends] == ["vote", "request"]


def test_palette_cycles_and_marker_is_per_palette_color() -> None:
    program = compile_source(
        """Processes {
  p
  q
}

Messages {
  m0 := "0"
  m1 := "1"
  m2 := "2"
  m3 := "3"
}

History {
  s0 := Send(m3) :: p -> q
  Recv(s0) :: q
}
"""
    )
    root = _parse(render_svg(program))

    # message_type 3 cycles back to palette index 0 (steel blue, marker a1).
    arrow = [
        e
        for e in _elements(root, "line")
        if e.attrib.get("marker-end") not in (None, "url(#t)")
    ][0]
    assert arrow.attrib["stroke"] == "#5b7fa6"
    assert arrow.attrib["marker-end"] == "url(#a1)"
    marker_ids = {marker.attrib["id"] for marker in _elements(root, "marker")}
    assert marker_ids == {"t", "a1"}


def test_caption_geometry_for_two_processes() -> None:
    program = compile_source(
        """Processes {
  p
  q
}

Messages {
  m := "hello"
}

History {
  m1 := Send(m) :: p -> q
  m2 := Send(m) :: q -> p
  Recv(m1) :: q
  Recv(m2) :: p
}
"""
    )
    root = _parse(render_svg(program))

    # One used message type: caption_y0 = 80 + 100 + 60 = 240, single entry
    # at y = 240, H = 240 + 0 + 20 = 260.
    assert root.attrib["viewBox"] == "0 0 360 260"
    caption = _caption(root)
    assert caption is not None
    entries = list(caption)
    assert len(entries) == 2
    swatch, text = entries
    assert swatch.tag == NS + "rect"
    assert swatch.attrib["y"] == "233"
    assert text.tag == NS + "text"
    assert text.attrib["y"] == "240"
    assert text.text == "m"


def test_empty_history_renders_lifelines_only() -> None:
    program = compile_source("Processes {\n  p\n}\n")
    root = _parse(render_svg(program))

    assert root.attrib["viewBox"] == "0 0 360 120"
    assert len(_elements(root, "circle")) == 0
    assert len(_elements(root, "line")) == 1


def test_self_send_received_draws_loop() -> None:
    program = compile_source(
        """Processes {
  p
}

Messages {
  m := "x"
}

History {
  s := Send(m) :: p -> p
  Recv(s) :: p
}
"""
    )
    root = _parse(render_svg(program))

    loops = [
        p for p in _elements(root, "path") if p.attrib.get("fill") == "none"
    ]
    assert len(loops) == 1
    assert loops[0].attrib["d"] == "M 73 86 C 77 118, 101 118, 105 86"


def test_self_send_lost_draws_dashed_stub_without_recv_dot() -> None:
    program = compile_source(
        """Processes {
  p
}

Messages {
  m := "x"
}

History {
  s := Send(m) :: p -> p
}
"""
    )
    root = _parse(render_svg(program))

    dashed = [e for e in _elements(root, "line") if "stroke-dasharray" in e.attrib]
    assert len(dashed) == 1
    assert dashed[0].attrib["x1"] == dashed[0].attrib["x2"] == "70"
    # Only the send dot exists; no recv dot.
    assert len(_elements(root, "circle")) == 1


def test_multicast_all_lost_draws_one_dashed_arrow_per_recipient() -> None:
    program = compile_source(
        """Processes {
  p
  q
  r
}

Messages {
  m := "x"
}

History {
  s := Send(m) :: p -> q, r
}
"""
    )
    root = _parse(render_svg(program))

    dashed = [e for e in _elements(root, "line") if "stroke-dasharray" in e.attrib]
    assert [(e.attrib["x1"], e.attrib["y1"], e.attrib["x2"], e.attrib["y2"]) for e in dashed] == [
        ("70", "85", "70", "172"),
        ("70", "85", "70", "272"),
    ]
    assert len(_elements(root, "circle")) == 1


def test_payload_special_chars_do_not_leak_into_svg() -> None:
    program = compile_source(
        """Processes {
  p
  q
}

Messages {
  m := "a <b> & c"
}

History {
  s := Send(m) :: p -> q
  Recv(s) :: q
}
"""
    )
    svg_text = render_svg(program)
    root = _parse(svg_text)  # must stay parseable
    # The caption carries the message name, not the payload.
    caption = _caption(root)
    assert caption is not None
    texts = [e for e in caption if e.tag == NS + "text"]
    assert [t.text for t in texts] == ["m"]
    assert "a <b> & c" not in svg_text


def test_cli_to_svg_prints_svg(capsys) -> None:
    exit_code = main(["--to-svg", str(ROOT / "example.st")])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.startswith("<svg ")
    assert captured.out.rstrip().endswith("</svg>")
    assert "== refined ast ==" not in captured.out
    assert captured.err == ""


def test_cli_default_prints_svg(capsys) -> None:
    exit_code = main([str(ROOT / "example.st")])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.startswith("<svg ")
    assert captured.out.rstrip().endswith("</svg>")
    assert captured.err == ""
