from pathlib import Path

import pytest

from spacetime import SemanticError
from spacetime.v2 import (
    MaybeBlockRefined,
    RecvEventRefined,
    RefinedHistoryItem,
    SendEventRefined,
    compile_source,
)

FIXTURES = Path(__file__).parent / "fixtures" / "v2"


INVALID_CASES = {
    "duplicate_event_across_maybe.st": "duplicate event declaration: 'm1'",
    "undeclared_message_in_maybe.st": "undeclared message: 'ack'",
    "undeclared_process_in_maybe.st": "undeclared process: 'z'",
    "undefined_event_in_maybe.st": "undeclared send event: 'm9'",
    "later_event_in_maybe.st": "undeclared send event: 'm1'",
    "recv_not_recipient_in_maybe.st": "process 'r' is not a recipient of send event 'm1'",
    "repeated_history.st": "duplicate History block",
}


@pytest.mark.parametrize(
    "filename, message",
    INVALID_CASES.items(),
    ids=INVALID_CASES.keys(),
)
def test_invalid_v2_programs(filename: str, message: str) -> None:
    source = (FIXTURES / "invalid" / filename).read_text()

    with pytest.raises(SemanticError, match=message):
        compile_source(source, source_name=filename)


def test_all_invalid_v2_fixtures_are_covered() -> None:
    expected = set(INVALID_CASES) | {"syntax_error_maybe.st"}
    found = {path.name for path in (FIXTURES / "invalid").glob("*.st")}
    assert found == expected


def _flatten(items: list[RefinedHistoryItem]) -> list:
    """Flatten a refined history tree into its events, depth-first."""
    events = []
    for item in items:
        if isinstance(item, MaybeBlockRefined):
            events.extend(_flatten(item.items))
        else:
            events.append(item)
    return events


def test_maybe_tree_shape_is_preserved() -> None:
    program = compile_source((FIXTURES / "valid" / "maybe_middle.st").read_text())

    items = program.history.items
    assert [type(item) for item in items] == [
        SendEventRefined,
        MaybeBlockRefined,
        RecvEventRefined,
    ]
    maybe = items[1]
    assert isinstance(maybe, MaybeBlockRefined)
    assert [type(item) for item in maybe.items] == [SendEventRefined, RecvEventRefined]


def test_temporal_positions_are_flattened_source_order() -> None:
    program = compile_source((FIXTURES / "valid" / "maybe_middle.st").read_text())

    events = _flatten(program.history.items)
    assert [event.temporal_pos for event in events] == [0, 1, 2, 3]


def test_nested_maybe_positions() -> None:
    program = compile_source((FIXTURES / "valid" / "nested_maybe.st").read_text())

    events = _flatten(program.history.items)
    assert [event.temporal_pos for event in events] == [0, 1, 2, 3, 4, 5]

    outer = program.history.items[1]
    assert isinstance(outer, MaybeBlockRefined)
    inner = outer.items[1]
    assert isinstance(inner, MaybeBlockRefined)
    assert [event.temporal_pos for event in _flatten(inner.items)] == [2, 3]


def test_receive_inside_maybe_resolves_to_send_inside_maybe() -> None:
    program = compile_source((FIXTURES / "valid" / "maybe_middle.st").read_text())

    maybe = program.history.items[1]
    assert isinstance(maybe, MaybeBlockRefined)
    send, recv = maybe.items
    assert isinstance(send, SendEventRefined)
    assert isinstance(recv, RecvEventRefined)
    assert recv.related_send_event is send
    assert recv.temporal_pos > send.temporal_pos


def test_empty_maybe_is_valid() -> None:
    program = compile_source((FIXTURES / "valid" / "empty_maybe.st").read_text())

    maybe = program.history.items[0]
    assert isinstance(maybe, MaybeBlockRefined)
    assert maybe.items == []
    assert [event.temporal_pos for event in _flatten(program.history.items)] == [0, 1]


def test_empty_program_is_valid() -> None:
    program = compile_source("")

    assert program.process_declarations == []
    assert program.history.items == []


def test_semantic_error_has_source_name_and_location() -> None:
    path = FIXTURES / "invalid" / "undeclared_process_in_maybe.st"

    with pytest.raises(SemanticError) as exc_info:
        compile_source(path.read_text(), source_name=str(path))

    error = exc_info.value
    assert error.location is not None
    assert str(error).startswith(f"{path}:")
    assert "undeclared process: 'z'" in str(error)
