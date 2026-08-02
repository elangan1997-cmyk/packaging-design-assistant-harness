from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from packaging_assistant.models import PackagingContentSpec, PanelDefinition


@dataclass(frozen=True)
class ContentLayoutGeneration:
    svg: str
    spec: PackagingContentSpec
    panels: tuple[PanelDefinition, ...]
    validation: dict[str, Any]
    source_report: str
    missing_fields_report: str
    review_checklist: str

