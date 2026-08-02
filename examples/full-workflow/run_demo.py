#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from packaging_assistant.api import run_packaging_request  # noqa: E402


def _path(result: object, filename: str) -> str:
    for output in result.outputs:
        path = output.get("path", "")
        if Path(path).name == filename:
            return path
    raise RuntimeError(f"Missing output: {filename}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the deterministic A -> B -> Mock C workflow demo")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.output).resolve()

    structure = run_packaging_request(
        {
            "action": "structure_template",
            "request_id": "demo-structure",
            "parameters": {
                "model_code": "锁底盒",
                "dimensions": {"length": 80, "width": 40, "height": 120, "unit": "mm"},
            },
        },
        root / "01-structure",
    )
    if not structure.success:
        raise RuntimeError(structure.error)

    content = run_packaging_request(
        {
            "action": "content_layout",
            "request_id": "demo-content",
            "parameters": {
                "template": _path(structure, "template.svg"),
                "brief": str(Path(__file__).with_name("demo-brief.json")),
            },
        },
        root / "02-content",
    )
    if not content.success:
        raise RuntimeError(content.error)

    mockup = run_packaging_request(
        {
            "action": "mockup_render",
            "request_id": "demo-mockup",
            "parameters": {
                "artwork": _path(content, "content-layout.svg"),
                "dimensions": {"length": 80, "width": 40, "height": 120, "unit": "mm"},
                "structure": "lock-bottom folding carton",
                "material": "350 gsm SBS paperboard",
                "finishes": [{"type": "foil", "target": "brand mark"}],
                "allow_mock": True,
                "config": {
                    "providers": [{"name": "mock", "type": "mock", "enabled": True}]
                },
            },
        },
        root / "03-mockup-contract",
    )
    if not mockup.success:
        raise RuntimeError(mockup.error)

    summary = {
        "success": True,
        "warning": "The final image is a deterministic Mock Provider contract fixture, not a real CMF render.",
        "stages": [
            {"action": structure.action, "status": structure.status, "job_id": structure.job_id},
            {"action": content.action, "status": content.status, "job_id": content.job_id},
            {"action": mockup.action, "status": mockup.status, "job_id": mockup.job_id},
        ],
    }
    (root / "workflow-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
