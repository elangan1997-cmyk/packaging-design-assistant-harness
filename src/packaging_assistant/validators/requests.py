from __future__ import annotations

from packaging_assistant.capabilities import ACTIONS
from packaging_assistant.exceptions import RequestValidationError
from packaging_assistant.models import PackagingRequest


def validate_request(request: PackagingRequest) -> None:
    if not request.action:
        raise RequestValidationError(
            "MISSING_REQUIRED_FIELD",
            "缺少 action。",
            {"missing_fields": ["action"]},
        )
    if request.action not in ACTIONS:
        raise RequestValidationError(
            "UNSUPPORTED_ACTION",
            f"不支持的 action：{request.action}",
            {"supported_actions": sorted(ACTIONS)},
        )

