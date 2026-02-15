#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

REQ_FILE="${SCRIPT_DIR}/requirements.txt"
PY_SCRIPT="${SCRIPT_DIR}/first_configuration.py"
VENV_DIR="${PROJECT_ROOT}/.venv"

# Find python command
if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
elif command -v py >/dev/null 2>&1; then
  PYTHON="py -3"
else
  echo "❌ Python not found. Install Python 3: https://www.python.org/downloads/"
  exit 1
fi

echo "ℹ️  Using Python: ${PYTHON}"

# Create venv if missing
if [[ ! -d "${VENV_DIR}" ]]; then
  echo "ℹ️  Creating virtualenv at ${VENV_DIR}"
  # shellcheck disable=SC2086
  ${PYTHON} -m venv "${VENV_DIR}"
fi

# Pick venv python path (mac/linux vs windows)
if [[ -f "${VENV_DIR}/bin/python" ]]; then
  VENV_PY="${VENV_DIR}/bin/python"
elif [[ -f "${VENV_DIR}/Scripts/python.exe" ]]; then
  VENV_PY="${VENV_DIR}/Scripts/python.exe"
else
  echo "❌ Could not find venv python interpreter."
  exit 1
fi

echo "ℹ️  Installing dependencies from ${REQ_FILE} into venv"
"${VENV_PY}" -m pip install -r "${REQ_FILE}"

echo "✅ Dependencies installed."

echo "ℹ️  Running: ${PY_SCRIPT}"
"${VENV_PY}" "${PY_SCRIPT}"