from __future__ import annotations

from packaging_assistant.providers.base import ModelCapabilities, Provider, ProviderRequest, ProviderResponse


class MockProvider(Provider):
    name = "mock"
    capabilities = ModelCapabilities(text=True, vision=True, image_generation=True, search=True)

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            success=True,
            provider=self.name,
            output={"mock": True, "operation": request.operation, "payload": request.payload},
        )

