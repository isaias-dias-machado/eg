from pathlib import Path

import pytest

from spacetime import ParseError
from spacetime.v2 import parse

FIXTURES = Path(__file__).parent / "fixtures" / "v2"


@pytest.mark.parametrize(
    "path",
    sorted((FIXTURES / "valid").glob("*.st")),
    ids=lambda path: path.name,
)
def test_valid_v2_examples_parse(path: Path) -> None:
    parse(path.read_text(), source_name=str(path))


def test_v2_grammar_loads_independent_of_cwd(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    parse("History {\n  Maybe {\n  }\n}\n")


def test_v2_syntax_error_has_location_and_context() -> None:
    source = (FIXTURES / "invalid" / "syntax_error_maybe.st").read_text()

    with pytest.raises(ParseError) as exc_info:
        parse(source, source_name="broken.st")

    error = exc_info.value
    assert error.location is not None
    assert error.source_name == "broken.st"
    assert "syntax error" in str(error)
    assert "^" in str(error)
