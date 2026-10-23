from pathlib import Path

import pytest

from spacetime import (
    RecvEventRefined,
    SemanticError,
    compile_source,
)

FIXTURES = Path(__file__).parent / "fixtures"


INVALID_CASES = {
    "duplicate_message.st": "duplicate message declaration: 'request'",
    "duplicate_process.st": "duplicate process declaration: 'p'",
    "duplicate_event.st": "duplicate event declaration: 'm1'",
    "repeated_processes.st": "duplicate Processes block",
    "repeated_messages.st": "duplicate Messages block",
    "repeated_history.st": "duplicate History block",
    "undeclared_message.st": "undeclared message: 'request'",
    "undeclared_send_sender.st": "undeclared process: 'p'",
    "undeclared_send_recipient.st": "undeclared process: 'q'",
    "undeclared_recv_process.st": "undeclared process: 'r'",
    "undefined_event.st": "undeclared send event: 'm9'",
    "later_event.st": "receive refers to send event declared later: 'm1'",
    "recv_not_recipient.st": "process 'r' is not a recipient of send event 'm1'",
}


@pytest.mark.parametrize(
    "filename, message",
    INVALID_CASES.items(),
    ids=INVALID_CASES.keys(),
)
def test_invalid_programs(filename: str, message: str) -> None:
    source = (FIXTURES / "invalid" / filename).read_text()

    with pytest.raises(SemanticError, match=message):
        compile_source(source, source_name=filename)


def test_undefined_and_later_event_errors_are_distinct() -> None:
    undefined = (FIXTURES / "invalid" / "undefined_event.st").read_text()
    later = (FIXTURES / "invalid" / "later_event.st").read_text()

    with pytest.raises(SemanticError) as undefined_error:
        compile_source(undefined)
    with pytest.raises(SemanticError) as later_error:
        compile_source(later)

    assert str(undefined_error.value) != str(later_error.value)
    assert "undeclared" in str(undefined_error.value)
    assert "declared later" in str(later_error.value)


def test_missing_history_is_valid() -> None:
    program = compile_source(
        """Processes {
  p
}
"""
    )

    assert program.history.events == []


def test_empty_program_is_valid() -> None:
    program = compile_source("")

    assert program.process_declarations == []
    assert program.history.events == []


def test_multicast_receive_stays_one_event() -> None:
    program = compile_source(
        """Processes {
  p
  q
}

Messages {
  request := "x"
}

History {
  m1 := Send(request) :: p -> p, q
  Recv(m1) :: p, q
}
"""
    )

    receives = [
        event
        for event in program.history.events
        if isinstance(event, RecvEventRefined)
    ]

    assert len(receives) == 1
    assert receives[0].process_ids == ["p", "q"]


def test_temporal_positions_come_from_event_order() -> None:
    program = compile_source(
        """Processes {
  p
  q
}

Messages {
  request := "x"
}

History {
  m1 := Send(request) :: p -> q
  Recv(m1) :: q
  m2 := Send(request) :: q -> p
}
"""
    )

    assert [event.temporal_pos for event in program.history.events] == [0, 1, 2]
    assert len(program.history.events) == 3


def test_process_order_is_preserved_in_refined_ast() -> None:
    program = compile_source(
        """Processes {
  p
  q
  r
}
"""
    )

    assert program.process_declarations == ["p", "q", "r"]


def test_semantic_error_has_source_name_and_location(compile_fixture) -> None:
    path = FIXTURES / "invalid" / "duplicate_process.st"

    with pytest.raises(SemanticError) as exc_info:
        compile_fixture(path)

    error = exc_info.value
    assert error.location is not None
    assert error.location.line == 3
    assert error.location.column == 3
    assert str(error).startswith(f"{path}:3:3:")
    assert "duplicate process declaration" in str(error)


def test_all_invalid_fixtures_are_covered(invalid_fixtures) -> None:
    expected = set(INVALID_CASES) | {"syntax_error.st"}
    assert {path.name for path in invalid_fixtures} == expected


def test_refined_send_does_not_keep_event_name() -> None:
    program = compile_source(
        """Processes {
  p
  q
}

Messages {
  request := "x"
}

History {
  m1 := Send(request) :: p -> q
}
"""
    )

    send = program.history.events[0]
    assert not hasattr(send, "name")
