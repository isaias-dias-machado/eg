import pytest

from spacetime import SemanticError, build_ast, parse


def build(source: str):
    return build_ast(parse(source))


def test_process_order_is_preserved() -> None:
    ast = build(
        """Processes {
  p
  q
  r
}
"""
    )

    assert [declaration.name for declaration in ast.process_declarations] == [
        "p",
        "q",
        "r",
    ]


def test_missing_history_is_an_empty_history() -> None:
    ast = build(
        """Processes {
  p
}
"""
    )

    assert ast.history.events == []


def test_empty_program_is_valid() -> None:
    ast = build("")

    assert ast.process_declarations == []
    assert ast.message_declarations == []
    assert ast.history.events == []


def test_duplicate_process_declaration_has_location() -> None:
    source = """Processes {
  p
  p
}
"""

    with pytest.raises(SemanticError, match="duplicate process declaration: 'p'") as exc_info:
        build(source)

    assert exc_info.value.location is not None
    assert exc_info.value.location.line == 3


def test_duplicate_message_declaration() -> None:
    source = """Messages {
  request := "one"
  request := "two"
}
"""

    with pytest.raises(SemanticError, match="duplicate message declaration: 'request'"):
        build(source)


@pytest.mark.parametrize(
    "source, message",
    [
        (
            """Processes {
  p
}

Processes {
  q
}
""",
            "duplicate Processes block",
        ),
        (
            """Messages {
  request := "one"
}

Messages {
  ack := "two"
}
""",
            "duplicate Messages block",
        ),
        (
            """History {
}

History {
}
""",
            "duplicate History block",
        ),
    ],
)
def test_repeated_blocks_are_errors(source: str, message: str) -> None:
    with pytest.raises(SemanticError, match=message):
        build(source)


def test_message_value_has_only_outer_quotes_removed() -> None:
    ast = build(
        """Messages {
  request := "hello"
}
"""
    )

    assert ast.message_declarations[0].value == "hello"


def test_raw_events_do_not_carry_temporal_positions() -> None:
    ast = build(
        """History {
  m1 := Send(request) :: p -> q
}
"""
    )

    assert not hasattr(ast.history.events[0], "temporal_pos")
