"""Command-line entry point: compile one DSL file and print its result."""

import argparse
import sys

from .compiler import compile_file
from .errors import DslError
from .render import format_ast, format_parse_tree, format_refined_ast
from .svg import render_svg

_STAGE_TITLES = {
    "parse": "parse tree",
    "ast": "ast",
    "refined": "refined ast",
}

_EPILOG = """\
the language: three blocks, in any order

  Processes { p  q }            declare process names, one per line
  Messages  { m := "payload" }  declare a message name and its payload text
  History   { ... }             the events, in the order they happen

History events:

  m1 := Send(msg) :: p -> q, r  process p sends message `msg` to q and r
  Recv(m1) :: q                 process q receives the message sent as m1

super simple example (save as hello.st, then run `spacetime hello.st`):

  Processes {
    p
    q
  }

  Messages {
    hello := "Hello"
  }

  History {
    m1 := Send(hello) :: p -> q
    Recv(m1) :: q
  }
"""


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
    """Compile the file named on the command line and print its SVG diagram.

    By default the SVG space-time diagram of the program is printed to
    stdout. With ``--print-stages``, only the frontend runs: the parse tree
    and both intermediate ASTs are printed as the pipeline produces them,
    and no SVG is rendered.

    Returns a process exit code: ``0`` on success, ``1`` when the file
    cannot be read or the program contains a DSL error. Diagnostics go to
    stderr; rendered output goes to stdout.
    """
    parser = argparse.ArgumentParser(
        prog="space-time-dsl",
        description="Compile a space-time diagram DSL file and print its SVG diagram.",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", help="DSL source file")
    parser.add_argument(
        "--print-stages",
        action="store_true",
        help="run only the frontend: print the parse tree and intermediate ASTs after every compiler stage",
    )
    parser.add_argument(
        "--to-svg",
        action="store_true",
        help="print the SVG space-time diagram (this is the default)",
    )
    args = parser.parse_args(argv)

    try:
        program = compile_file(
            args.path,
            observe=_print_stage if args.print_stages else None,
        )
    except (DslError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1

    if not args.print_stages:
        # write, not print: render_svg already ends with a newline, and the
        # golden file docs/sample_v2.svg must diff byte-exact against this
        # output.
        sys.stdout.write(render_svg(program))
    return 0
