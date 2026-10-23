from pathlib import Path

import pytest
from lark import Tree

from spacetime import (
    Ast,
    RefinedAst,
    SemanticError,
    compile_file,
    compile_source,
)

ROOT = Path(__file__).parents[1]


def test_compile_source_end_to_end() -> None:
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
}
"""
    )

    assert program.process_declarations == ["p", "q"]
    assert len(program.history.events) == 2


def test_compile_source_reports_every_stage() -> None:
    seen: list[tuple[str, object]] = []

    compile_source(
        """Processes {
  p
}

Messages {
  request := "x"
}

History {
  m1 := Send(request) :: p -> p
}
""",
        observe=lambda stage, output: seen.append((stage, output)),
    )

    assert [stage for stage, _ in seen] == ["parse", "ast", "refined"]
    assert isinstance(seen[0][1], Tree)
    assert isinstance(seen[1][1], Ast)
    assert isinstance(seen[2][1], RefinedAst)


def test_example_txt_compiles() -> None:
    program = compile_file(ROOT / "example.txt")

    assert program.process_declarations == ["p", "q", "r"]
    assert len(program.history.events) == 6


def test_all_valid_fixtures_compile(valid_fixtures, compile_fixture) -> None:
    for path in valid_fixtures:
        compile_fixture(path)


def test_compile_file_uses_path_as_source_name() -> None:
    path = ROOT / "tests" / "fixtures" / "invalid" / "duplicate_process.st"

    with pytest.raises(SemanticError) as exc_info:
        compile_file(path)

    assert str(exc_info.value).startswith(f"{path}:")
