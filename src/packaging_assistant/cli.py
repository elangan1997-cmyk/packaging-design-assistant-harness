from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from packaging_assistant.api import run_packaging_request
from packaging_assistant.models.ir import json_ready


def _read_json(path_value: str) -> dict[str, Any]:
    payload = json.loads(Path(path_value).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object")
    return payload


def _print_result(result: object) -> None:
    print(json.dumps(json_ready(result), ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="packaging-assistant")
    parser.add_argument("--output", help="Job workspace root")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect = sub.add_parser("inspect", help="Inspect a packaging asset")
    inspect.add_argument("input")

    route = sub.add_parser("route", help="Resolve a request without executing providers")
    route.add_argument("input", help="Request JSON file")

    structure = sub.add_parser("structure", help="Generate a deterministic structure template")
    structure.add_argument("--spec", required=True)

    content = sub.add_parser("content", help="Place packaging content into a structure template")
    content.add_argument("--template", required=True)
    content.add_argument("--brief", required=True)

    mockup = sub.add_parser("mockup", help="Render a CMF mockup through a configured provider")
    mockup.add_argument("--artwork", required=True)
    mockup.add_argument("--config")

    run = sub.add_parser("run", help="Run a unified job request")
    run.add_argument("--job", required=True)
    run.add_argument("--dry-run", action="store_true")

    validate = sub.add_parser("validate", help="Validate JSON or SVG input")
    validate.add_argument("file")

    sub.add_parser("health-check", help="Check the local harness")
    return parser


def request_from_args(args: argparse.Namespace) -> tuple[dict[str, Any], bool]:
    if args.command == "inspect":
        return {"action": "inspect", "parameters": {"input": args.input}}, False
    if args.command == "route":
        payload = _read_json(args.input)
        return payload, True
    if args.command == "structure":
        spec = _read_json(args.spec)
        return {"action": "structure_template", "parameters": spec}, False
    if args.command == "content":
        return {
            "action": "content_layout",
            "parameters": {"template": args.template, "brief": args.brief},
        }, False
    if args.command == "mockup":
        return {
            "action": "mockup_render",
            "parameters": {"artwork": args.artwork, "config": args.config},
        }, False
    if args.command == "run":
        return _read_json(args.job), bool(args.dry_run)
    if args.command == "validate":
        return {"action": "validate", "parameters": {"file": args.file}}, False
    if args.command == "health-check":
        return {"action": "health_check", "parameters": {}}, False
    raise ValueError(f"Unknown command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        request, dry_run = request_from_args(args)
        result = run_packaging_request(request, args.output, dry_run=dry_run)
        _print_result(result)
        return 0 if result.success else 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        _print_result(
            {
                "success": False,
                "status": "failed",
                "error": {"code": "CLI_INPUT_ERROR", "message": str(exc)},
            }
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
