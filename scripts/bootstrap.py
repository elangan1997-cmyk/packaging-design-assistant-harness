#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    venv = root / ".venv"
    if not venv.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    python = venv / "bin" / "python"
    subprocess.run([str(python), "-m", "pip", "install", "-e", str(root)], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

