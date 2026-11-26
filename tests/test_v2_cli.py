from pathlib import Path

from spacetime.cli import main

ROOT = Path(__file__).parents[1]
V2_FIXTURES = ROOT / "tests" / "fixtures" / "v2"


def test_cli_compiles_maybe_file(capsys) -> None:
    path = V2_FIXTURES / "valid" / "maybe_middle.st"

    exit_code = main([str(path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "maybe_block_refined" in captured.out
    assert "== parse tree ==" not in captured.out
    assert captured.err == ""


def test_cli_prints_every_stage_when_requested(capsys) -> None:
    path = V2_FIXTURES / "valid" / "maybe_middle.st"

    exit_code = main(["--print-stages", str(path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "== parse tree ==" in captured.out
    assert "== ast ==" in captured.out
    assert "== refined ast ==" in captured.out
    assert "maybe_block" in captured.out
    assert captured.err == ""


def test_cli_reports_semantic_error(capsys) -> None:
    path = V2_FIXTURES / "invalid" / "duplicate_event_across_maybe.st"

    exit_code = main([str(path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "duplicate event declaration: 'm1'" in captured.err
    assert str(path) in captured.err


def test_cli_compiles_example_file(capsys) -> None:
    exit_code = main([str(ROOT / "example.txt")])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "refined_ast" in captured.out
    assert captured.err == ""
