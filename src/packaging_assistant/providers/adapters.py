from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from packaging_assistant.providers.base import (
    ModelCapabilities,
    Provider,
    ProviderConfig,
    ProviderRequest,
    ProviderResponse,
)


def _sanitized_error(code: str, message: str, status: int | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if status is not None:
        error["status"] = status
    return error


class HostProvider(Provider):
    """Adapter for capabilities supplied by the current agent host."""

    def __init__(
        self,
        name: str,
        capabilities: ModelCapabilities,
        callback: Callable[[ProviderRequest], ProviderResponse] | None = None,
    ) -> None:
        self.name = name
        self.capabilities = capabilities
        self._callback = callback

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        if request.dry_run:
            return ProviderResponse(True, self.name, {"dry_run": True})
        if self._callback is None:
            return ProviderResponse(
                False,
                self.name,
                error=_sanitized_error(
                    "HOST_CAPABILITY_UNAVAILABLE",
                    "当前宿主没有向 Python Harness 注册该能力。",
                ),
            )
        return self._callback(request)


class RESTProvider(Provider):
    """JSON-over-HTTP provider with environment-only secret resolution."""

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self.name = config.name
        self.capabilities = config.capabilities

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.config.api_key_env:
            secret = os.environ.get(self.config.api_key_env)
            if not secret:
                return headers
            headers["Authorization"] = f"Bearer {secret}"
        return headers

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        if request.dry_run:
            return ProviderResponse(True, self.name, {"dry_run": True})
        if not self.config.endpoint:
            return ProviderResponse(
                False,
                self.name,
                error=_sanitized_error("PROVIDER_NOT_CONFIGURED", "Provider endpoint 未配置。"),
            )
        if self.config.api_key_env and not os.environ.get(self.config.api_key_env):
            return ProviderResponse(
                False,
                self.name,
                error=_sanitized_error(
                    "PROVIDER_CREDENTIAL_MISSING",
                    f"缺少环境变量：{self.config.api_key_env}",
                ),
            )
        body = json.dumps(
            {
                "model": self.config.model,
                "operation": request.operation,
                "input": request.payload,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        http_request = urllib.request.Request(
            self.config.endpoint,
            data=body,
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=self.config.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (TimeoutError, socket.timeout) as exc:
            return ProviderResponse(
                False,
                self.name,
                error=_sanitized_error("PROVIDER_TIMEOUT", "Provider 请求超时。"),
                retryable=True,
            )
        except urllib.error.HTTPError as exc:
            retryable = exc.code == 429 or exc.code >= 500
            return ProviderResponse(
                False,
                self.name,
                error=_sanitized_error("PROVIDER_HTTP_ERROR", "Provider 返回 HTTP 错误。", exc.code),
                retryable=retryable,
            )
        except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError):
            return ProviderResponse(
                False,
                self.name,
                error=_sanitized_error("PROVIDER_REQUEST_FAILED", "Provider 请求失败或返回无效 JSON。"),
                retryable=True,
            )
        if not isinstance(payload, dict):
            return ProviderResponse(
                False,
                self.name,
                error=_sanitized_error("INVALID_PROVIDER_RESPONSE", "Provider 响应必须是 JSON 对象。"),
            )
        return ProviderResponse(True, self.name, output=payload)


class OpenAICompatibleProvider(RESTProvider):
    """Configurable OpenAI-compatible JSON endpoint; no endpoint is hard-coded."""


class CustomRESTProvider(RESTProvider):
    """Configurable custom REST endpoint using the Harness provider envelope."""

