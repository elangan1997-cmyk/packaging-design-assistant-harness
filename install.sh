#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}

"$PYTHON_BIN" -m venv "$PROJECT_DIR/.venv"
"$PROJECT_DIR/.venv/bin/python" -m pip install --upgrade pip
"$PROJECT_DIR/.venv/bin/python" -m pip install -e "$PROJECT_DIR"
"$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/scripts/health_check.py"

echo "Installed. CLI: $PROJECT_DIR/.venv/bin/packaging-assistant"

