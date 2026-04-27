#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"
PORT="${PORT:-8501}"
ADDRESS="${ADDRESS:-0.0.0.0}"

cd "$ROOT_DIR"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Local virtualenv not found at .venv."
  echo "Create it with: python3 -m venv .venv"
  exit 1
fi

if ! "$VENV_PYTHON" -c "import streamlit, matplotlib" >/dev/null 2>&1; then
  echo "Installing required packages into .venv..."
  "$VENV_PYTHON" -m pip install -r requirements.txt
fi

mkdir -p "$ROOT_DIR/.matplotlib"
export MPLCONFIGDIR="$ROOT_DIR/.matplotlib"

echo "Starting Golf Simulator on http://localhost:$PORT"
echo "If localhost does not load, try http://127.0.0.1:$PORT"
exec "$VENV_PYTHON" -m streamlit run app.py --server.address "$ADDRESS" --server.port "$PORT"
