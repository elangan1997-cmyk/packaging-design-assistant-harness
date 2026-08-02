#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ -d "$PROJECT_DIR/.venv" ]; then
  rm -r "$PROJECT_DIR/.venv"
fi

echo "Removed the project-local virtual environment. Source files and outputs were kept."

