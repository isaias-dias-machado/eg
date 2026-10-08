#!/usr/bin/env bash
set -euo pipefail

echo "Setting up Python project..."

# Move to the repository root
cd "$(dirname "$0")"

# Check that Python is installed
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 is not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# Install dependencies using the venv's Python
echo "Installing dependencies..."
.venv/bin/python -m pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo "Activate your environment with:"
echo "source .venv/bin/activate"

