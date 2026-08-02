from __future__ import annotations

from pathlib import Path
from typing import Any

from packaging_assistant.models import PackagingAsset, PackagingRequest, PackagingResult
from packaging_assistant.modules.content import generate_content_layout
from packaging_assistant.modules.mockup import generate_mockup
from packaging_assistant.orchestrator import run_request
from packaging_assistant.parsers import inspect_asset
from packaging_assistant.modules.structure import generate_structure_template


def run_packaging_request(
    request: dict[str, Any] | PackagingRequest,
    output_dir: str | Path | None = None,
    *,
    dry_run: bool = False,
) -> PackagingResult:
    """Run one isolated packaging job through the stable request contract."""
    return run_request(request, output_dir, dry_run=dry_run)


def inspect_packaging_asset(path: str | Path) -> PackagingAsset:
    return inspect_asset(path)


__all__ = [
    "generate_content_layout",
    "generate_mockup",
    "generate_structure_template",
    "inspect_packaging_asset",
    "run_packaging_request",
]
