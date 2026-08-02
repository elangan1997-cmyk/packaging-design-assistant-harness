#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from packaging_assistant.api import generate_content_layout, generate_structure_template  # noqa: E402


STRUCTURE_OUTPUTS = ["structure_spec.json", "template.svg", "validation_report.json"]
CONTENT_OUTPUTS = [
    "content-layout.svg",
    "content-spec.json",
    "missing-fields.md",
    "review-checklist.md",
    "source-report.md",
]
MOCKUP_OUTPUTS = [
    "cmf-plan.json",
    "generation-record.json",
    "mockup.png",
    "retry-record.json",
    "review-checklist.md",
    "visual-qa.json",
]


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _case(
    case_id: str,
    module: str,
    description: str,
    job: dict[str, Any],
    assertions: dict[str, Any],
    expectation: dict[str, Any],
) -> Path:
    root = REPOSITORY_ROOT / "evals" / case_id
    (root / "input").mkdir(parents=True, exist_ok=True)
    (root / "expected").mkdir(parents=True, exist_ok=True)
    _write_json(root / "job.json", job)
    _write_json(root / "assertions.json", assertions)
    _write_json(root / "expected" / "expectation.json", expectation)
    (root / "README.md").write_text(
        "\n".join(
            [
                f"# {case_id}",
                "",
                f"- Module: {module}",
                f"- Input: {description}",
                f"- Expected route: `{expectation['route']}`",
                f"- Expected tools: {', '.join(f'`{item}`' for item in expectation['tools'])}",
                f"- Expected outputs: {', '.join(f'`{item}`' for item in expectation['outputs']) or 'none'}",
                f"- Expected warnings: {', '.join(f'`{item}`' for item in expectation['warnings']) or 'none'}",
                f"- Pass condition: {expectation['pass_condition']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return root


def _template(path: Path, model: str = "锁底盒") -> str:
    generation = generate_structure_template(
        {
            "model_code": model,
            "dimensions": {"length": 80, "width": 40, "height": 120, "unit": "mm"},
        }
    )
    target = path / "input" / "template.svg"
    target.write_text(generation.svg, encoding="utf-8")
    return "${CASE}/input/template.svg"


def _brief(path: Path, full: bool = False) -> str:
    payload: dict[str, Any] = {
        "jurisdiction": "CN",
        "brand": {"name": "测试品牌"},
        "product": {"name": "观赏鱼专用盐", "net_content": "500 g"},
    }
    if full:
        payload["manufacturer"] = {
            "name": "用户提供的生产企业",
            "address": "用户提供的生产地址",
            "license_number": "用户提供的许可证编号",
        }
        payload["standards"] = {"execution_standard": "用户提供的执行标准"}
    target = path / "input" / "brief.json"
    _write_json(target, payload)
    return "${CASE}/input/brief.json"


def _completed_artwork(path: Path) -> str:
    template_ref = _template(path)
    template = Path(template_ref.replace("${CASE}", str(path)))
    generation = generate_content_layout(
        {
            "template": str(template),
            "brief": {
                "jurisdiction": "CN",
                "brand": {"name": "测试品牌"},
                "product": {"name": "观赏鱼专用盐", "net_content": "500 g"},
            },
        }
    )
    target = path / "input" / "completed-artwork.svg"
    target.write_text(generation.svg, encoding="utf-8")
    return "${CASE}/input/completed-artwork.svg"


def build() -> None:
    dimensions = {"length": 80, "width": 40, "height": 120, "unit": "mm"}
    for case_id, model in (("a01-lock-bottom", "锁底盒"), ("a02-carry-handle", "手提盒")):
        _case(
            case_id,
            "A",
            f"{model} with 80 x 40 x 120 mm",
            {"action": "structure_template", "parameters": {"model_code": model, "dimensions": dimensions}},
            {"success": True, "status": "completed", "output_names": STRUCTURE_OUTPUTS},
            {
                "route": "structure_template",
                "tools": ["deterministic geometry", "SVG validator"],
                "outputs": STRUCTURE_OUTPUTS,
                "warnings": ["REQUIRES_MANUFACTURER_REVIEW"],
                "pass_condition": "deterministic SVG and validation outputs are produced",
            },
        )
    _case(
        "a03-missing-model",
        "A",
        "dimensions without a box model",
        {"action": "structure_template", "parameters": {"dimensions": dimensions}},
        {"success": False, "status": "needs_input", "error_code": "MISSING_REQUIRED_FIELD"},
        {
            "route": "clarification_required",
            "tools": ["model registry"],
            "outputs": [],
            "warnings": [],
            "pass_condition": "returns one model-choice prompt and preserves dimensions",
        },
    )
    _case(
        "a04-unimplemented-model",
        "A",
        "registered straight box model",
        {"action": "structure_template", "parameters": {"model_code": "直线盒", "dimensions": dimensions}},
        {"success": False, "status": "not_implemented", "error_code": "NOT_IMPLEMENTED"},
        {
            "route": "structure_template",
            "tools": ["model registry"],
            "outputs": [],
            "warnings": [],
            "pass_condition": "does not substitute another box geometry",
        },
    )

    for case_id, description, full in (
        ("b01-placeholders", "minimal product brief", False),
        ("b02-sourced-enterprise", "user-provided enterprise and standard fields", True),
        ("b03-structure-protection", "content insertion with protected dieline layers", False),
        ("b04-safe-panel-layout", "content placement across semantic non-glue panels", True),
    ):
        root = _case(
            case_id,
            "B",
            description,
            {"action": "content_layout", "parameters": {}},
            {"success": True, "status": "completed", "output_names": CONTENT_OUTPUTS},
            {
                "route": "content_layout",
                "tools": ["SVG parser", "field generator", "safe-area layout", "structure fingerprint"],
                "outputs": CONTENT_OUTPUTS,
                "warnings": ["REQUIRES_COMPLIANCE_REVIEW"],
                "pass_condition": "sources/statuses are present and protected structure layers remain unchanged",
            },
        )
        template = _template(root)
        brief = _brief(root, full)
        _write_json(root / "job.json", {"action": "content_layout", "parameters": {"template": template, "brief": brief}})

    mock_root = _case(
        "c01-mock-provider-contract",
        "C",
        "completed artwork with explicit Mock opt-in",
        {"action": "mockup_render", "parameters": {}},
        {"success": True, "status": "manual_review", "output_names": MOCKUP_OUTPUTS, "warnings_contains": ["MOCK_OUTPUT_NOT_A_REAL_CMF_RENDER"]},
        {
            "route": "mockup_render",
            "tools": ["VisionProvider", "ImageGenerationProvider", "visual QA"],
            "outputs": MOCKUP_OUTPUTS,
            "warnings": ["MOCK_OUTPUT_NOT_A_REAL_CMF_RENDER"],
            "pass_condition": "six outputs are produced and Mock never reports a real render",
        },
    )
    artwork = _completed_artwork(mock_root)
    config = mock_root / "input" / "mock-provider.json"
    _write_json(
        config,
        {
            "providers": [{"name": "mock", "type": "mock", "enabled": True}],
            "mockup": {"allow_mock": True},
        },
    )
    _write_json(
        mock_root / "job.json",
        {
            "action": "mockup_render",
            "parameters": {
                "artwork": artwork,
                "dimensions": dimensions,
                "material": "350 gsm SBS paperboard",
                "finishes": [{"type": "foil", "target": "brand mark"}],
                "config": "${CASE}/input/mock-provider.json",
            },
        },
    )

    for case_id, description, params, status, error_code, route in (
        (
            "c02-provider-unavailable",
            "completed artwork without configured providers",
            {"dimensions": dimensions, "material": "paperboard"},
            "failed",
            "PROVIDER_UNAVAILABLE",
            "mockup_render",
        ),
        (
            "c03-missing-dimensions",
            "completed artwork without physical dimensions",
            {"material": "paperboard"},
            "needs_input",
            "MISSING_REQUIRED_FIELD",
            "clarification_required",
        ),
        (
            "c04-blank-dieline-conflict",
            "blank dieline requested as a finished mockup",
            {"dimensions": dimensions, "material": "paperboard"},
            "needs_input",
            "MISSING_REQUIRED_FIELD",
            "clarification_required",
        ),
    ):
        root = _case(
            case_id,
            "C",
            description,
            {"action": "mockup_render", "parameters": {}},
            {"success": False, "status": status, "error_code": error_code},
            {
                "route": route,
                "tools": ["asset classifier", "capability router"],
                "outputs": [],
                "warnings": [],
                "pass_condition": "fails explicitly before any unapproved or invalid render",
            },
        )
        asset = _template(root) if case_id == "c04-blank-dieline-conflict" else _completed_artwork(root)
        _write_json(root / "job.json", {"action": "mockup_render", "parameters": {"artwork": asset, **params}})


if __name__ == "__main__":
    build()
    print("Generated 12 evaluation cases.")
