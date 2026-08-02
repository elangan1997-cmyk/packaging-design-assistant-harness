#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

EVAL_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = EVAL_ROOT.parent
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from packaging_assistant.api import run_packaging_request  # noqa: E402


def _resolve(value: Any, case_root: Path) -> Any:
    if isinstance(value, str):
        return value.replace("${CASE}", str(case_root))
    if isinstance(value, dict):
        return {key: _resolve(item, case_root) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve(item, case_root) for item in value]
    return value


def _output_names(result: object) -> list[str]:
    outputs = getattr(result, "outputs", [])
    return sorted(Path(item.get("path", item.get("name", ""))).name for item in outputs)


def run_case(case_root: Path) -> tuple[bool, list[str]]:
    job = _resolve(json.loads((case_root / "job.json").read_text(encoding="utf-8")), case_root)
    expected = json.loads((case_root / "assertions.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        result = run_packaging_request(job, Path(tmp) / "jobs")
        if result.success != expected["success"]:
            failures.append(f"success={result.success!r}")
        if result.status != expected["status"]:
            failures.append(f"status={result.status!r}")
        if "error_code" in expected and (result.error or {}).get("code") != expected["error_code"]:
            failures.append(f"error_code={(result.error or {}).get('code')!r}")
        if "output_names" in expected and _output_names(result) != sorted(expected["output_names"]):
            failures.append(f"outputs={_output_names(result)!r}")
        for warning in expected.get("warnings_contains", []):
            if warning not in result.warnings:
                failures.append(f"missing_warning={warning!r}")
    return not failures, failures


def main() -> int:
    cases = sorted(path for path in EVAL_ROOT.iterdir() if path.is_dir() and (path / "job.json").is_file())
    results = []
    for case in cases:
        passed, failures = run_case(case)
        results.append({"case": case.name, "passed": passed, "failures": failures})
    payload = {
        "total": len(results),
        "passed": sum(item["passed"] for item in results),
        "failed": sum(not item["passed"] for item in results),
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["total"] == 12 and payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
