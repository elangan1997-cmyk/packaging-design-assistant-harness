from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from packaging_assistant.models import VisualQAResult


@dataclass(frozen=True)
class MockupGeneration:
    image_bytes: bytes
    mime_type: str
    cmf_plan: dict[str, Any]
    generation_record: dict[str, Any]
    visual_qa: VisualQAResult
    retry_record: dict[str, Any]
    review_checklist: str
    warnings: tuple[str, ...]
    status: str

