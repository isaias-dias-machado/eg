from pathlib import Path

import pytest

from spacetime import ParseError, parse

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    "path",
    sorted((FIXTURES / "valid").glob("*.st")),
    ids=lambda path: path.name,
)
def test_valid_examples_parse(path: Path) -> None:
    parse(path.read_text(), source_name=str(path))


def test_grammar_loads_independent_of_cwd(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    parse("Processes {\n  p\n}\n")


def test_syntax_error_has_location_and_context() -> None:
    source = (FIXTURES / "invalid" / "syntax_error.st").read_text()

    with pytest.raises(ParseError) as exc_info:
        parse(source, source_name="broken.st")

    error = exc_info.value
    assert error.location is not None
    assert error.location.line == 3
    assert error.location.column == 1
    assert error.source_name == "broken.st"
    assert "syntax error" in str(error)
    assert "p" in str(error)
    assert "^" in str(error)
