from __future__ import annotations

from typing import Any

from packaging_assistant.modules.structure.registry import model_report


ACTIONS: dict[str, dict[str, Any]] = {
    "health_check": {
        "module": "core",
        "implemented": True,
        "outputs": ["health_report.json"],
        "providers": [],
    },
    "inspect": {
        "module": "core",
        "implemented": True,
        "outputs": ["inspection.json"],
        "providers": [],
    },
    "route": {
        "module": "core",
        "implemented": True,
        "outputs": ["route.json"],
        "providers": [],
    },
    "validate": {
        "module": "core",
        "implemented": True,
        "outputs": ["validation.json"],
        "providers": [],
    },
    "structure_template": {
        "module": "structure",
        "implemented": True,
        "outputs": ["template.svg", "structure_spec.json", "validation_report.json"],
        "providers": [],
        "note": "Model-specific availability; see structure_models.",
    },
    "content_layout": {
        "module": "content",
        "implemented": True,
        "outputs": [
            "content-layout.svg",
            "content-spec.json",
            "source-report.md",
            "missing-fields.md",
            "review-checklist.md",
        ],
        "providers": [],
        "note": "Deterministic sourced-field placement; external compliance research is not automatic.",
    },
    "mockup_render": {
        "module": "mockup",
        "implemented": True,
        "outputs": [
            "mockup.png",
            "cmf-plan.json",
            "generation-record.json",
            "visual-qa.json",
            "retry-record.json",
            "review-checklist.md",
        ],
        "providers": ["image_generation", "vision"],
        "note": "Provider orchestration is implemented; a real configured provider is required for a real render.",
    },
}


def is_implemented(action: str) -> bool:
    return bool(ACTIONS.get(action, {}).get("implemented"))


def capability_report() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "actions": {name: dict(value) for name, value in sorted(ACTIONS.items())},
        "structure_models": model_report(),
        "core_requires_node": False,
        "web_required": False,
        "paid_providers_called_by_default": False,
    }
