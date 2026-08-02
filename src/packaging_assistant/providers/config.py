from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from packaging_assistant.exceptions import RequestValidationError
from packaging_assistant.providers.adapters import CustomRESTProvider, HostProvider, OpenAICompatibleProvider
from packaging_assistant.providers.base import ModelCapabilities, Provider, ProviderConfig
from packaging_assistant.providers.mock import MockProvider


def load_provider_config(value: object) -> dict[str, Any]:
    """Load provider settings from a dict, JSON, or YAML file without resolving secrets."""
    if value in (None, ""):
        return {"providers": []}
    if isinstance(value, dict):
        return dict(value)
    if not isinstance(value, (str, Path)):
        raise RequestValidationError("INVALID_PROVIDER_CONFIG", "config 必须是对象或配置文件路径。")
    path = Path(value).expanduser()
    if not path.is_file():
        raise RequestValidationError("INPUT_NOT_FOUND", f"Provider 配置不存在：{path}")
    text = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() == ".json":
            payload = json.loads(text)
        else:
            import yaml

            payload = yaml.safe_load(text)
    except (ValueError, ImportError) as exc:
        raise RequestValidationError("INVALID_PROVIDER_CONFIG", "Provider 配置无法解析。") from exc
    if not isinstance(payload, dict):
        raise RequestValidationError("INVALID_PROVIDER_CONFIG", "Provider 配置根节点必须是对象。")
    return payload


def _capabilities(raw: object) -> ModelCapabilities:
    values = raw if isinstance(raw, dict) else {}
    return ModelCapabilities(
        text=bool(values.get("text")),
        vision=bool(values.get("vision")),
        image_generation=bool(values.get("image_generation")),
        search=bool(values.get("search")),
        tool_calling=bool(values.get("tool_calling")),
        structured_output=bool(values.get("structured_output")),
        file_reading=bool(values.get("file_reading")),
    )


def build_providers(config: dict[str, Any]) -> list[Provider]:
    """Build providers in declared priority order; disabled entries are skipped."""
    raw_providers = config.get("providers", [])
    if isinstance(raw_providers, dict):
        raw_providers = [dict(value, name=name) for name, value in raw_providers.items() if isinstance(value, dict)]
    if not isinstance(raw_providers, list):
        raise RequestValidationError("INVALID_PROVIDER_CONFIG", "providers 必须是数组或对象。")
    providers: list[Provider] = []
    for index, raw in enumerate(raw_providers):
        if not isinstance(raw, dict) or not bool(raw.get("enabled", True)):
            continue
        provider_type = str(raw.get("type", raw.get("provider_type", ""))).strip().lower()
        name = str(raw.get("name", f"provider-{index + 1}"))
        capabilities = _capabilities(raw.get("capabilities"))
        if provider_type == "mock":
            providers.append(MockProvider())
            continue
        if provider_type == "host":
            providers.append(HostProvider(name, capabilities))
            continue
        try:
            provider_config = ProviderConfig(
                name=name,
                provider_type=provider_type,
                model=str(raw.get("model", "")),
                endpoint=str(raw.get("endpoint", "")),
                api_key_env=str(raw.get("api_key_env", "")),
                enabled=True,
                may_incur_cost=bool(raw.get("may_incur_cost", True)),
                timeout_seconds=float(raw.get("timeout_seconds", 60)),
                max_retries=int(raw.get("max_retries", 0)),
                capabilities=capabilities,
            )
        except (TypeError, ValueError) as exc:
            raise RequestValidationError(
                "INVALID_PROVIDER_CONFIG", f"Provider 数值配置无效：{name}"
            ) from exc
        if provider_type == "openai_compatible":
            providers.append(OpenAICompatibleProvider(provider_config))
        elif provider_type == "custom_rest":
            providers.append(CustomRESTProvider(provider_config))
        else:
            raise RequestValidationError("UNKNOWN_PROVIDER_TYPE", f"未知 Provider 类型：{provider_type}")
    return providers
