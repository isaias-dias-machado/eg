"""Command-line entry point: compile one DSL file and print its result."""

import argparse
import sys

from .compiler import compile_file
from .errors import DslError
from .render import format_refined_ast


def main(argv: list[str] | None = None) -> int:
    """Compile the file named on the command line and print its refined AST.

    Returns a process exit code: ``0`` on success, ``1`` when the file
    cannot be read or the program contains a DSL error. Diagnostics go to
    stderr; the rendered AST goes to stdout.
    """
    parser = argparse.ArgumentParser(prog="space-time-dsl")
    parser.add_argument("path", help="DSL source file")
    args = parser.parse_args(argv)

    try:
        program = compile_file(args.path)
    except (DslError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1

    print(format_refined_ast(program))
    return 0
