from pathlib import Path

import pytest
from lark import Tree

from spacetime import SemanticError
from spacetime.v2 import Ast, RefinedAst, compile_file, compile_source

ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "v2"


def test_compile_source_end_to_end_v2() -> None:
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
  Maybe {
    Recv(m1) :: q
  }
}
"""
    )

    assert program.process_declarations == ["p", "q"]
    assert len(program.history.items) == 2


def test_compile_source_reports_every_stage() -> None:
    seen: list[tuple[str, object]] = []

    compile_source(
        """History {
  Maybe {
  }
}
""",
        observe=lambda stage, output: seen.append((stage, output)),
    )

    assert [stage for stage, _ in seen] == ["parse", "ast", "refined"]
    assert isinstance(seen[0][1], Tree)
    assert isinstance(seen[1][1], Ast)
    assert isinstance(seen[2][1], RefinedAst)


def test_all_valid_v2_fixtures_compile() -> None:
    for path in sorted((FIXTURES / "valid").glob("*.st")):
        compile_source(path.read_text(), source_name=str(path))


def test_compile_file_uses_path_as_source_name() -> None:
    path = FIXTURES / "invalid" / "repeated_history.st"

    with pytest.raises(SemanticError) as exc_info:
        compile_file(path)

    assert str(exc_info.value).startswith(f"{path}:")
