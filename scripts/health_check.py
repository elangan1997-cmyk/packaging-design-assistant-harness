#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from packaging_assistant.api import run_packaging_request  # noqa: E402
from packaging_assistant.models.ir import json_ready  # noqa: E402


def main() -> int:
    result = run_packaging_request({"action": "health_check", "parameters": {}})
    print(json.dumps(json_ready(result), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())

