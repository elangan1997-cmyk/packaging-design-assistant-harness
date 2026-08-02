from __future__ import annotations

import base64
import hashlib
import json

from packaging_assistant.providers.base import ModelCapabilities, Provider, ProviderRequest, ProviderResponse


# A fixed 1x1 transparent PNG used only as a deterministic provider-contract fixture.
MOCK_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUB"
    "AScY42YAAAAASUVORK5CYII="
)


class MockProvider(Provider):
    name = "mock"
    capabilities = ModelCapabilities(
        text=True,
        vision=True,
        image_generation=True,
        search=True,
        tool_calling=True,
        structured_output=True,
        file_reading=True,
    )

    def __init__(self, scripted: list[ProviderResponse] | None = None) -> None:
        self.calls: list[ProviderRequest] = []
        self._scripted = list(scripted or [])

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        self.calls.append(request)
        if self._scripted:
            return self._scripted.pop(0)
        canonical = json.dumps(request.payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(f"{request.operation}:{canonical}".encode("utf-8")).hexdigest()
        if request.operation == "visual_qa":
            output = {
                "passed": True,
                "score": 1.0,
                "issues": [],
                "recommended_action": "accept",
                "mock": True,
                "request_digest": digest,
            }
        elif request.operation == "image_generation":
            output = {
                "image_base64": MOCK_PNG_BASE64,
                "mime_type": "image/png",
                "mock": True,
                "request_digest": digest,
            }
        elif request.operation == "search":
            output = {"results": [], "mock": True, "request_digest": digest}
        else:
            output = {"mock": True, "request_digest": digest}
        return ProviderResponse(
            success=True,
            provider=self.name,
            output=output,
        )

    @staticmethod
    def image_bytes() -> bytes:
        return base64.b64decode(MOCK_PNG_BASE64)
