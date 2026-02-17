#!/usr/bin/env bash
# Launcher for destroy_infrastructure.py on Mac/Linux.
# Ensures .venv exists at project root, installs requirements, then runs the Python script.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REQ_FILE="$SCRIPT_DIR/requirements.txt"
PY_SCRIPT="$SCRIPT_DIR/destroy_infrastructure.py"
VENV_DIR="$PROJECT_ROOT/.venv"

# ----------------------------------------
# Find Python
# ----------------------------------------

if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "❌ Python not found. Install Python 3: https://www.python.org/downloads/"
    exit 1
fi

echo "ℹ️  Using Python: $PYTHON"

# ----------------------------------------
# Create venv if missing
# ----------------------------------------

if [ ! -d "$VENV_DIR" ]; then
    echo "ℹ️  Creating virtualenv at $VENV_DIR"
    "$PYTHON" -m venv "$VENV_DIR"
fi

# ----------------------------------------
# Venv python (Mac/Linux: bin/python)
# ----------------------------------------

VENV_PY="$VENV_DIR/bin/python"
if [ ! -x "$VENV_PY" ]; then
    echo "❌ Could not find venv python at $VENV_PY"
    exit 1
fi

# ----------------------------------------
# Install dependencies
# ----------------------------------------

echo "ℹ️  Installing dependencies from $REQ_FILE into venv"
"$VENV_PY" -m pip install -q -r "$REQ_FILE"
echo "✅ Dependencies installed."

# ----------------------------------------
# Run destroy script
# ----------------------------------------

echo "ℹ️  Running: $PY_SCRIPT"
"$VENV_PY" "$PY_SCRIPT"
echo "✅ Script completed successfully."
