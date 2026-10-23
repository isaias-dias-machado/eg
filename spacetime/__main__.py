"""Entry point for ``python -m spacetime <file>``.

Mirrors the ``spacetime`` console script declared in pyproject.toml; both
delegate to :func:`spacetime.cli.main`, whose return value is the exit code.
"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
