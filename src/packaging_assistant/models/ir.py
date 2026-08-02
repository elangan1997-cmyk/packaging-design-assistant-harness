from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AssetKind(str, Enum):
    SVG = "svg"
    IMAGE = "image"
    PDF = "pdf"
    JSON = "json"
    YAML = "yaml"
    TEXT = "text"
    UNKNOWN = "unknown"


@dataclass
class PackagingAsset:
    path: str
    type: str = AssetKind.UNKNOWN.value
    role: str = "input"
    exists: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PackagingRequest:
    action: str
    request_id: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PackagingRequest":
        if not isinstance(data, dict):
            raise TypeError("request must be a JSON object")
        return cls(
            action=str(data.get("action", "")).strip(),
            request_id=str(data.get("request_id", "")).strip(),
            parameters=data.get("parameters") if isinstance(data.get("parameters"), dict) else {},
        )


@dataclass
class RouteDecision:
    action: str
    module: str
    implemented: bool
    reason: str
    required_capabilities: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    input_assets: list[PackagingAsset] = field(default_factory=list)
    providers: list[str] = field(default_factory=list)
    may_incur_cost: bool = False
    expected_outputs: list[str] = field(default_factory=list)
    manual_review_items: list[str] = field(default_factory=list)
    choice_prompt: dict[str, Any] | None = None


@dataclass
class ValidationIssue:
    code: str
    message: str
    severity: str = "error"
    field: str | None = None


@dataclass
class ValidationReport:
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class PackagingJob:
    workflow: str
    request_id: str = ""
    job_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    status: str = "pending"
    jurisdiction: str = "CN"
    product_category: str = ""
    assets: list[PackagingAsset] = field(default_factory=list)
    structure: dict[str, Any] = field(default_factory=dict)
    content: dict[str, Any] = field(default_factory=dict)
    finishes: list[dict[str, Any]] = field(default_factory=list)
    providers: dict[str, Any] = field(default_factory=dict)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    manual_review_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PackagingResult:
    success: bool
    action: str
    request_id: str
    status: str
    job_id: str = ""
    outputs: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    manual_review_required: bool = True
    error: dict[str, Any] | None = None
    route: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "to_dict"):
        return json_ready(value.to_dict())
    if hasattr(value, "__dataclass_fields__"):
        return json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    return value
