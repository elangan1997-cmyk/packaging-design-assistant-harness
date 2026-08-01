from __future__ import annotations

from typing import Any


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
        "implemented": False,
        "outputs": ["template.svg", "structure_spec.json", "validation_report.json"],
        "providers": [],
        "note": "Pending tested deterministic model implementations.",
    },
    "content_layout": {
        "module": "content",
        "implemented": False,
        "outputs": ["content_layout.svg", "content_spec.json", "review_report.json"],
        "providers": [],
        "note": "Module B is not implemented in Phase 1.",
    },
    "mockup_render": {
        "module": "mockup",
        "implemented": False,
        "outputs": ["mockup.png", "visual_qa.json"],
        "providers": ["image_generation", "vision"],
        "note": "CMF guidance remains available; executable rendering providers are not configured.",
    },
}


def is_implemented(action: str) -> bool:
    return bool(ACTIONS.get(action, {}).get("implemented"))


def capability_report() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "actions": {name: dict(value) for name, value in sorted(ACTIONS.items())},
        "core_requires_node": False,
        "web_required": False,
        "paid_providers_called_by_default": False,
    }

