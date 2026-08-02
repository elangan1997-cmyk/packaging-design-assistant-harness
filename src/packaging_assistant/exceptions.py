from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PackagingAssistantError(Exception):
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, **self.details}


class RequestValidationError(PackagingAssistantError):
    pass


class NotImplementedCapabilityError(PackagingAssistantError):
    pass

