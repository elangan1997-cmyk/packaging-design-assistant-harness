from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelCapabilities:
    text: bool = False
    vision: bool = False
    image_generation: bool = False
    search: bool = False
    tool_calling: bool = False
    structured_output: bool = False
    file_reading: bool = False

    def supports(self, capability: str) -> bool:
        """Return whether this provider advertises a named capability."""
        return bool(getattr(self, capability, False))


@dataclass(frozen=True)
class ProviderConfig:
    """Non-secret provider settings; credentials are referenced by env-var name only."""

    name: str
    provider_type: str
    model: str = ""
    endpoint: str = ""
    api_key_env: str = ""
    enabled: bool = True
    may_incur_cost: bool = False
    timeout_seconds: float = 60.0
    max_retries: int = 0
    capabilities: ModelCapabilities = ModelCapabilities()


@dataclass
class ProviderRequest:
    operation: str
    payload: dict[str, Any] = field(default_factory=dict)
    dry_run: bool = False


@dataclass
class ProviderResponse:
    success: bool
    provider: str
    output: dict[str, Any] = field(default_factory=dict)
    error: dict[str, Any] | None = None
    attempt: int = 1
    retryable: bool = False


class Provider(ABC):
    name: str
    capabilities: ModelCapabilities

    @abstractmethod
    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        raise NotImplementedError


class LLMProvider(Provider, ABC):
    """Marker interface for text model providers."""


class VisionProvider(Provider, ABC):
    """Provider capable of visually inspecting packaging assets."""

    def analyze(self, request: ProviderRequest) -> ProviderResponse:
        return self.invoke(request)


class ImageGenerationProvider(Provider, ABC):
    """Provider capable of producing an externally generated packaging image."""

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        return self.invoke(request)


class SearchProvider(Provider, ABC):
    """Provider capable of retrieving source-backed research."""

    def search(self, request: ProviderRequest) -> ProviderResponse:
        return self.invoke(request)
