"""Command-line entry point: compile one DSL file and print its result."""

import argparse
import sys

from .compiler import compile_file
from .errors import DslError
from .render import format_ast, format_parse_tree, format_refined_ast
from .v2 import compile_file as compile_file_v2

_STAGE_TITLES = {
    "parse": "parse tree",
    "ast": "ast",
    "refined": "refined ast",
}


def _print_stage(stage: str, output: object) -> None:
    """Print one compiler stage with a header identifying the stage."""
    renderers = {
        "parse": format_parse_tree,
        "ast": format_ast,
        "refined": format_refined_ast,
    }
    print(f"== {_STAGE_TITLES[stage]} ==")
    print(renderers[stage](output))


def main(argv: list[str] | None = None) -> int:
    """Compile the file named on the command line and print its refined AST.

    With ``--print-stages``, the parse tree and both intermediate ASTs are
    printed as the pipeline produces them, and the final refined AST is not
    printed a second time.

    Returns a process exit code: ``0`` on success, ``1`` when the file
    cannot be read or the program contains a DSL error. Diagnostics go to
    stderr; rendered trees go to stdout.
    """
    parser = argparse.ArgumentParser(prog="space-time-dsl")
    parser.add_argument("path", help="DSL source file")
    parser.add_argument(
        "--v2",
        action="store_true",
        help="compile with the v2 language (adds Maybe blocks to History)",
    )
    parser.add_argument(
        "--print-stages",
        action="store_true",
        help="print the parse tree and intermediate ASTs after every compiler stage",
    )
    args = parser.parse_args(argv)

    compile = compile_file_v2 if args.v2 else compile_file

    try:
        program = compile(
            args.path,
            observe=_print_stage if args.print_stages else None,
        )
    except (DslError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1

    if not args.print_stages:
        print(format_refined_ast(program))
    return 0
