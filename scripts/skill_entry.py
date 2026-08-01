#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
    parser = argparse.ArgumentParser(description="Packaging Design Assistant Skill entrypoint")
    parser.add_argument("--request", required=True, help="Unified request JSON")
    parser.add_argument("--output", required=True, help="Job workspace root")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        payload = json.loads(Path(args.request).read_text(encoding="utf-8"))
        result = run_packaging_request(payload, args.output, dry_run=args.dry_run)
        print(json.dumps(json_ready(result), ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result.success else 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "success": False,
                    "status": "failed",
                    "error": {"code": "ENTRY_INPUT_ERROR", "message": str(exc)},
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

