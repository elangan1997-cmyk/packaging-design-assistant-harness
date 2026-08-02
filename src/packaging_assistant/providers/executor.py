from __future__ import annotations

from dataclasses import dataclass, field

from packaging_assistant.providers.base import Provider, ProviderRequest, ProviderResponse


@dataclass
class ProviderExecution:
    response: ProviderResponse
    attempts: list[dict[str, object]] = field(default_factory=list)


class ProviderExecutor:
    """Execute providers in declared order with finite retries and explicit failure."""

    def __init__(self, providers: list[Provider]) -> None:
        self.providers = list(providers)

    def execute(
        self,
        capability: str,
        request: ProviderRequest,
        *,
        retries_per_provider: int = 0,
    ) -> ProviderExecution:
        attempts: list[dict[str, object]] = []
        eligible = [provider for provider in self.providers if provider.capabilities.supports(capability)]
        if not eligible:
            return ProviderExecution(
                ProviderResponse(
                    False,
                    "",
                    error={
                        "code": "PROVIDER_UNAVAILABLE",
                        "message": f"没有可用的 {capability} Provider。",
                    },
                ),
                attempts,
            )
        for provider in eligible:
            for attempt in range(1, max(0, retries_per_provider) + 2):
                response = provider.invoke(request)
                response.attempt = attempt
                attempts.append(
                    {
                        "provider": provider.name,
                        "operation": request.operation,
                        "attempt": attempt,
                        "success": response.success,
                        "error_code": (response.error or {}).get("code"),
                    }
                )
                if response.success:
                    return ProviderExecution(response, attempts)
                if not response.retryable:
                    break
        return ProviderExecution(
            ProviderResponse(
                False,
                eligible[-1].name,
                error={
                    "code": "PROVIDER_CHAIN_FAILED",
                    "message": f"所有 {capability} Provider 均未成功。",
                },
            ),
            attempts,
        )
