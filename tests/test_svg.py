"""Tests for the SVG backend (:func:`spacetime.svg.render_svg`).

Covers the golden example (``example.st`` vs ``docs/sample_v2.svg``), the
layout invariants from ``docs/svg_target.md``, the ``message_type``
declaration-index semantics, edge cases, and the ``--to-svg`` CLI flag.
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


def _strip_message_labels(root: ET.Element) -> ET.Element:
    """Remove italic message-label ``<text>`` elements in place.

    The golden file hand-tunes label text (abbreviated message names) and
    x positions, so the golden comparison masks them; label content and
    position are pinned by separate unit tests.
    """
    for parent in root.iter():
        for child in list(parent):
            if child.tag == NS + "text" and child.attrib.get("font-style") == "italic":
                parent.remove(child)
    return root


def _assert_same_tree(actual: ET.Element, expected: ET.Element, path: str = "/svg") -> None:
    assert actual.tag == expected.tag, path
    assert actual.attrib == expected.attrib, f"{path}: {actual.attrib} != {expected.attrib}"
    assert (actual.text or "").strip() == (expected.text or "").strip(), path
    assert len(actual) == len(expected), f"{path}: child count {len(actual)} != {len(expected)}"
    for index, (actual_child, expected_child) in enumerate(zip(actual, expected)):
        _assert_same_tree(actual_child, expected_child, f"{path}/{actual_child.tag}[{index}]")


def _elements(root: ET.Element, tag: str) -> list[ET.Element]:
    return root.findall(f".//{NS}{tag}")


def test_golden_example_matches_sample_v2() -> None:
    program = compile_file(ROOT / "example.st")
    rendered = render_svg(program)
    golden = (ROOT / "docs" / "sample_v2.svg").read_text()

    _assert_same_tree(
        _strip_message_labels(_parse(rendered)),
        _strip_message_labels(_parse(golden)),
    )


def test_golden_example_labels_carry_payloads() -> None:
    program = compile_file(ROOT / "example.st")
    root = _parse(render_svg(program))

    labels = [
        element
        for element in _elements(root, "text")
        if element.attrib.get("font-style") == "italic"
    ]
    assert [element.text for element in labels] == [
        "Request o que quiser",
        "Ack",
        "Request o que quiser",
    ]
    assert [element.attrib["fill"] for element in labels] == [
        "#5b7fa6",
        "#6f9a76",
        "#5b7fa6",
    ]


def test_lifelines_are_horizontal_and_in_declaration_order() -> None:
    root = _parse(render_svg(compile_file(ROOT / "example.st")))

    assert root.attrib["viewBox"] == "0 0 360 320"
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


def test_label_position_is_arrow_midpoint_plus_offset() -> None:
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

    # m1 arrow: (70, 85) -> (140, 175); midpoint (105, 130); label at +7, +4.
    labels = [
        element
        for element in _elements(root, "text")
        if element.attrib.get("font-style") == "italic"
    ]
    assert len(labels) == 2
    assert labels[0].attrib["x"] == "112"
    assert labels[0].attrib["y"] == "134"
    assert labels[0].text == "hello"


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


def test_payload_is_xml_escaped() -> None:
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
    labels = [
        element
        for element in _elements(root, "text")
        if element.attrib.get("font-style") == "italic"
    ]
    assert labels[0].text == "a <b> & c"
    assert "&lt;b&gt;" in svg_text
    assert "&amp;" in svg_text


def test_cli_to_svg_prints_svg(capsys) -> None:
    exit_code = main(["--to-svg", str(ROOT / "example.st")])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.startswith("<svg ")
    assert captured.out.rstrip().endswith("</svg>")
    assert "== refined ast ==" not in captured.out
    assert captured.err == ""


def test_cli_default_output_unchanged(capsys) -> None:
    exit_code = main([str(ROOT / "example.st")])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.startswith("refined_ast")
    assert "<svg" not in captured.out
