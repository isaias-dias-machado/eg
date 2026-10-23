from pathlib import Path

import pytest

from spacetime.cli import main

ROOT = Path(__file__).parents[1]


def test_cli_compiles_valid_file(capsys) -> None:
    exit_code = main([str(ROOT / "example.txt")])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "event_number 6" in captured.out
    assert "== parse tree ==" not in captured.out
    assert captured.err == ""


def test_cli_prints_every_stage_when_requested(capsys) -> None:
    exit_code = main(["--print-stages", str(ROOT / "example.txt")])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "== parse tree ==" in captured.out
    assert "== ast ==" in captured.out
    assert "== refined ast ==" in captured.out
    assert "event_number 6" in captured.out
    assert captured.err == ""


def test_cli_reports_semantic_error(capsys) -> None:
    path = ROOT / "tests" / "fixtures" / "invalid" / "duplicate_process.st"

    exit_code = main([str(path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "duplicate process declaration" in captured.err
    assert str(path) in captured.err


def test_cli_reports_missing_file(capsys) -> None:
    exit_code = main([str(ROOT / "does-not-exist.st")])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "does-not-exist.st" in captured.err


def test_cli_requires_a_path() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code == 2
