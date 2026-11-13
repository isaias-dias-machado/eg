from pathlib import Path

from spacetime.v2 import MaybeBlock, RecvEvent, SendEvent, build_ast, parse

FIXTURES = Path(__file__).parent / "fixtures" / "v2"


def test_maybe_block_keeps_tree_shape() -> None:
    tree = parse((FIXTURES / "valid" / "maybe_middle.st").read_text())
    ast = build_ast(tree)

    items = ast.history.items
    assert [type(item) for item in items] == [SendEvent, MaybeBlock, RecvEvent]

    maybe = items[1]
    assert isinstance(maybe, MaybeBlock)
    assert [type(item) for item in maybe.items] == [SendEvent, RecvEvent]
    assert maybe.location.line >= 1
    assert maybe.location.column >= 1


def test_nested_maybe_builds_nested_tree() -> None:
    tree = parse((FIXTURES / "valid" / "nested_maybe.st").read_text())
    ast = build_ast(tree)

    outer = ast.history.items[1]
    assert isinstance(outer, MaybeBlock)
    inner = outer.items[1]
    assert isinstance(inner, MaybeBlock)
    assert [type(item) for item in inner.items] == [SendEvent, RecvEvent]


def test_empty_maybe_builds_empty_block() -> None:
    tree = parse((FIXTURES / "valid" / "empty_maybe.st").read_text())
    ast = build_ast(tree)

    maybe = ast.history.items[0]
    assert isinstance(maybe, MaybeBlock)
    assert maybe.items == []
