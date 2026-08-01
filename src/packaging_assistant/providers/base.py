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


class Provider(ABC):
    name: str
    capabilities: ModelCapabilities

    @abstractmethod
    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        raise NotImplementedError
