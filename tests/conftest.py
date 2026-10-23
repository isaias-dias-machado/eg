from pathlib import Path

import pytest

from spacetime import compile_source

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def valid_fixtures() -> list[Path]:
    return sorted((FIXTURES / "valid").glob("*.st"))


@pytest.fixture
def invalid_fixtures() -> list[Path]:
    return sorted((FIXTURES / "invalid").glob("*.st"))


@pytest.fixture
def compile_fixture():
    def compile_path(path: Path):
        return compile_source(path.read_text(), source_name=str(path))

    return compile_path
