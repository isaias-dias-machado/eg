#!/usr/bin/env bash
set -euo pipefail

# Minimum interpreter: the code uses match statements and PEP 604 unions
# (`SendEvent | RecvEvent`), both of which need Python 3.10+.
PYTHON_MIN="3.10"

echo "Setting up Python project..."

# Move to the repository root
cd "$(dirname "$0")"

# --- Prerequisites ---------------------------------------------------------

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 is not installed." >&2
    exit 1
fi

if ! python3 -c "import sys
min_version = tuple(int(part) for part in '${PYTHON_MIN}'.split('.'))
sys.exit(0 if sys.version_info[:2] >= min_version else 1)"; then
    echo "Error: Python ${PYTHON_MIN} or newer is required, found $(python3 -V 2>&1)." >&2
    exit 1
fi

# --- Guard: no virtual environment created in place at the repo root ------

# `python3 -m venv .` (or `python3 -m venv <repo-root>`) unpacks bin/, include/,
# lib/, lib64 and pyvenv.cfg directly into the repository. That shadows .venv/
# and makes `source bin/activate` look legitimate while pointing at a venv that
# lacks the dev dependencies. .venv/pyvenv.cfg is expected; the root one is not.
if [ -f pyvenv.cfg ]; then
    echo "Error: found pyvenv.cfg at the repository root." >&2
    echo "This means a virtual environment was created in place instead of in .venv/." >&2
    echo "Remove the stray environment with:" >&2
    echo "    rm -rf bin include lib lib64 pyvenv.cfg" >&2
    echo "then run ./setup.sh again." >&2
    exit 1
fi

# --- Virtual environment --------------------------------------------------

# .venv/ is the only supported location (see .gitignore and README.md).
if [ -d .venv ] && [ ! -x .venv/bin/python ]; then
    echo "Error: .venv/ exists but has no working interpreter (incomplete creation?)." >&2
    echo "Remove it with 'rm -rf .venv' and run ./setup.sh again." >&2
    exit 1
fi

if [ -d .venv ]; then
    echo "Virtual environment already exists at .venv/."
else
    echo "Creating virtual environment at .venv/..."
    python3 -m venv .venv
fi

# --- Dependencies ---------------------------------------------------------

# Editable install: `import spacetime` resolves to this checkout, the
# `spacetime` console script is linked into .venv/bin/, and pytest can import
# the package without relying on the current directory. Runtime dependencies
# and the `dev` group (pytest) are declared in pyproject.toml.
echo "Installing the project in editable mode, with dev dependencies..."
.venv/bin/python -m pip install --editable . --group dev

echo ""
echo "Setup complete! Using $(.venv/bin/python -V 2>&1) from .venv/"
echo "Activate your environment with:"
echo "    source .venv/bin/activate"
echo ""
echo "Then compile a program with:  spacetime example.txt"
echo "And run the tests with:       pytest -q"
