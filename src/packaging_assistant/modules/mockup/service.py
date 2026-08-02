from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from packaging_assistant.exceptions import RequestValidationError
from packaging_assistant.models import VisualQAIssue, VisualQAResult
from packaging_assistant.parsers import inspect_asset
from packaging_assistant.providers import (
    MockProvider,
    Provider,
    ProviderExecutor,
    ProviderRequest,
    build_providers,
    load_provider_config,
)

from .models import MockupGeneration


PROTECTION_RULES = (
    "Do not redesign, redraw, translate, replace, or move the original artwork.",
    "Preserve logo geometry, Chinese text glyphs, product name, colors, layout, and panel mapping.",
    "Preserve the packaging structure and physical proportions.",
    "Do not show dielines, crease lines, safe-area guides, annotations, or finish callout boxes.",
    "Attach finish effects only to specified package surfaces with physically plausible reflections.",
    "This is a visualization, not a production or proofing file.",
)

QA_CHECKS = (
    "structure_or_proportion_changed",
    "artwork_or_main_visual_shifted",
    "logo_distorted",
    "chinese_text_redrawn_or_garbled",
    "panel_mapping_wrong",
    "transparent_window_missing",
    "finish_region_shifted_or_floating",
    "dieline_or_annotation_visible",
    "flexible_packaging_became_rigid",
    "bottle_or_label_deformed",
    "color_severely_shifted",
    "wrong_product_count",
    "camera_background_or_lighting_mismatch",
)


def _structure_protection_rules(structure: str) -> list[str]:
    normalized = structure.lower()
    rules: list[str] = []
    if any(token in normalized for token in ("pouch", "bag", "sachet", "flexible", "软包装", "袋")):
        rules.append(
            "Keep the package flexible with realistic seams and heat seals; do not apply decorative finishes on heat-seal areas."
        )
    if any(token in normalized for token in ("bottle", "jar", "瓶", "罐")):
        rules.append(
            "Preserve both the bottle geometry and the label geometry, placement, wrap, and label-to-container relationship."
        )
    return rules


def _dimensions(value: object) -> dict[str, float | str]:
    if not isinstance(value, dict):
        raise RequestValidationError("MISSING_PHYSICAL_DIMENSIONS", "生成最终效果图前必须提供实际包装尺寸。")
    normalized: dict[str, float | str] = {"unit": str(value.get("unit", "mm"))}
    for key in ("length", "width", "height"):
        try:
            number = float(value[key])
        except (KeyError, TypeError, ValueError) as exc:
            raise RequestValidationError(
                "MISSING_PHYSICAL_DIMENSIONS", "尺寸必须包含正数 length、width、height。"
            ) from exc
        if number <= 0:
            raise RequestValidationError("INVALID_DIMENSIONS", "包装尺寸必须大于 0。")
        normalized[key] = number
    return normalized


def _artwork(value: object) -> tuple[Path, bytes, dict[str, Any]]:
    if not isinstance(value, (str, Path)):
        raise RequestValidationError("MISSING_REQUIRED_FIELD", "缺少完成设计稿。", {"missing_fields": ["artwork"]})
    path = Path(value).expanduser()
    if not path.is_file():
        raise RequestValidationError("INPUT_NOT_FOUND", f"完成稿不存在：{path}")
    if path.suffix.lower() not in {".svg", ".pdf", ".png", ".jpg", ".jpeg"}:
        raise RequestValidationError("UNSUPPORTED_ASSET", "完成稿必须是 SVG、PDF、PNG 或 JPG。")
    asset = inspect_asset(path)
    if path.suffix.lower() == ".svg" and asset.role == "blank_structure_template":
        raise RequestValidationError(
            "BLANK_DIELINE_IS_NOT_ARTWORK",
            "当前文件是空白刀模；请先完成包装设计稿，再生成 CMF 效果图。",
        )
    raw = path.read_bytes()
    return path, raw, {"type": asset.type, "role": asset.role, **asset.metadata}


def _providers(parameters: dict[str, Any], config: dict[str, Any]) -> tuple[list[Provider], dict[str, Any]]:
    injected = parameters.get("_providers")
    if isinstance(injected, list) and all(isinstance(item, Provider) for item in injected):
        return list(injected), {"providers": [{"name": item.name, "type": "injected"} for item in injected]}
    providers = build_providers(config)
    return providers, config


def _guard_provider_use(providers: list[Provider], parameters: dict[str, Any]) -> None:
    if not providers:
        raise RequestValidationError("PROVIDER_UNAVAILABLE", "未配置 VisionProvider 和 ImageGenerationProvider。")
    if any(isinstance(provider, MockProvider) for provider in providers) and not bool(parameters.get("allow_mock")):
        raise RequestValidationError(
            "MOCK_PROVIDER_REQUIRES_OPT_IN",
            "Mock Provider 只用于测试；请明确设置 allow_mock=true。",
        )
    external = [provider for provider in providers if hasattr(provider, "config")]
    if external and not bool(parameters.get("allow_external_api")):
        raise RequestValidationError(
            "EXTERNAL_API_CONFIRMATION_REQUIRED",
            "外部 Provider 可能产生费用；请确认后设置 allow_external_api=true。",
            {"providers": [provider.name for provider in external]},
        )


def _visual_qa(output: dict[str, Any], provider: str) -> VisualQAResult:
    try:
        raw_issues = output.get("issues", [])
        issues = tuple(
            VisualQAIssue(
                type=str(item.get("type", "unknown")),
                severity=str(item.get("severity", "high")),
                region=str(item.get("region", "")),
                message=str(item.get("message", "")),
                retryable=bool(item.get("retryable")),
            )
            for item in raw_issues
            if isinstance(item, dict)
        )
        action = str(output.get("recommended_action", "manual_review"))
        if action not in {"accept", "retry", "manual_review", "reject"}:
            action = "manual_review"
        return VisualQAResult(
            passed=bool(output.get("passed")) and action == "accept",
            score=max(0.0, min(1.0, float(output.get("score", 0.0)))),
            issues=issues,
            recommended_action=action,
            provider=provider,
        )
    except (TypeError, ValueError):
        return VisualQAResult(
            passed=False,
            score=0.0,
            issues=(
                VisualQAIssue(
                    "invalid_qa_response",
                    "high",
                    "",
                    "视觉 Provider 未返回合法的 QA 结构。",
                    False,
                ),
            ),
            recommended_action="manual_review",
            provider=provider,
        )


def _image_bytes(output: dict[str, Any]) -> tuple[bytes, str]:
    encoded = output.get("image_base64")
    if not isinstance(encoded, str) or not encoded:
        raise RequestValidationError(
            "INVALID_PROVIDER_RESPONSE", "ImageGenerationProvider 必须返回 image_base64。"
        )
    try:
        return base64.b64decode(encoded, validate=True), str(output.get("mime_type", "image/png"))
    except ValueError as exc:
        raise RequestValidationError("INVALID_PROVIDER_RESPONSE", "image_base64 无法解码。") from exc


def generate_mockup(parameters: dict[str, Any]) -> MockupGeneration:
    """Generate a CMF visualization only through configured providers, then run independent visual QA."""
    provider_config = load_provider_config(parameters.get("config"))
    config_defaults = provider_config.get("mockup", {})
    effective = {**(config_defaults if isinstance(config_defaults, dict) else {}), **parameters}
    artwork_path, artwork_bytes, asset = _artwork(effective.get("artwork"))
    dimensions = _dimensions(effective.get("dimensions"))
    material = str(effective.get("material", "")).strip()
    if not material:
        raise RequestValidationError("MISSING_REQUIRED_FIELD", "缺少包装材质。", {"missing_fields": ["material"]})
    finishes = effective.get("finishes", [])
    if not isinstance(finishes, list):
        raise RequestValidationError("INVALID_PARAMETER", "finishes 必须是数组。")
    structure = str(effective.get("structure", asset.get("role", "")))
    protection_rules = [*PROTECTION_RULES, *_structure_protection_rules(structure)]
    providers, provider_config = _providers(effective, provider_config)
    _guard_provider_use(providers, effective)
    executor = ProviderExecutor(providers)

    max_qa_retries = int(effective.get("max_qa_retries", 2))
    if max_qa_retries < 0 or max_qa_retries > 2:
        raise RequestValidationError("INVALID_PARAMETER", "max_qa_retries 必须在 0 到 2 之间。")
    provider_retries = int(effective.get("provider_retries", 1))
    if provider_retries < 0 or provider_retries > 2:
        raise RequestValidationError("INVALID_PARAMETER", "provider_retries 必须在 0 到 2 之间。")

    artwork_sha256 = hashlib.sha256(artwork_bytes).hexdigest()
    artwork_payload = {
        "filename": artwork_path.name,
        "mime_hint": artwork_path.suffix.lower(),
        "artwork_base64": base64.b64encode(artwork_bytes).decode("ascii"),
        "artwork_sha256": artwork_sha256,
        "asset": asset,
        "dimensions": dimensions,
    }
    inspection = executor.execute(
        "vision",
        ProviderRequest(
            "artwork_inspection",
            {
                **artwork_payload,
                "instructions": protection_rules,
                "required_observations": ["logo", "Chinese text", "panel mapping", "dielines", "finish masks"],
            },
        ),
        retries_per_provider=provider_retries,
    )
    if not inspection.response.success:
        raise RequestValidationError(
            "VISION_PROVIDER_FAILED",
            "完成稿视觉检查失败。",
            {"attempts": inspection.attempts},
        )

    cmf_plan = {
        "schema_version": "1.0",
        "artwork_sha256": artwork_sha256,
        "dimensions": dimensions,
        "structure": structure,
        "material": material,
        "finishes": finishes,
        "camera": effective.get("camera", "three-quarter product view"),
        "background": effective.get("background", "neutral studio background"),
        "protection_rules": protection_rules,
        "production_file": False,
    }
    attempts: list[dict[str, Any]] = []
    final_image = b""
    mime_type = "image/png"
    qa_result = VisualQAResult(False, 0.0, (), "manual_review")
    correction_notes: list[str] = []

    for qa_attempt in range(max_qa_retries + 1):
        generation = executor.execute(
            "image_generation",
            ProviderRequest(
                "image_generation",
                {
                    **artwork_payload,
                    "cmf_plan": cmf_plan,
                    "inspection": inspection.response.output,
                    "correction_notes": correction_notes,
                },
            ),
            retries_per_provider=provider_retries,
        )
        attempts.extend(generation.attempts)
        if not generation.response.success:
            raise RequestValidationError(
                "IMAGE_GENERATION_PROVIDER_FAILED",
                "效果图 Provider 未成功。",
                {"attempts": attempts},
            )
        final_image, mime_type = _image_bytes(generation.response.output)
        qa = executor.execute(
            "vision",
            ProviderRequest(
                "visual_qa",
                {
                    "original_artwork_sha256": artwork_sha256,
                    "original_artwork_base64": artwork_payload["artwork_base64"],
                    "generated_image_base64": base64.b64encode(final_image).decode("ascii"),
                    "cmf_plan": cmf_plan,
                    "checks": list(QA_CHECKS),
                },
            ),
            retries_per_provider=provider_retries,
        )
        attempts.extend(qa.attempts)
        if not qa.response.success:
            qa_result = VisualQAResult(
                False,
                0.0,
                (VisualQAIssue("qa_provider_failed", "high", "", "视觉 QA Provider 失败。", False),),
                "manual_review",
                qa.response.provider,
            )
            break
        qa_result = _visual_qa(qa.response.output, qa.response.provider)
        attempts.append(
            {
                "stage": "visual_qa_decision",
                "qa_attempt": qa_attempt + 1,
                "passed": qa_result.passed,
                "recommended_action": qa_result.recommended_action,
            }
        )
        if qa_result.passed or qa_result.recommended_action != "retry":
            break
        correction_notes = [issue.message for issue in qa_result.issues if issue.retryable]

    mock_used = any(isinstance(provider, MockProvider) for provider in providers)
    status = "completed" if qa_result.passed and not mock_used else "manual_review"
    warnings = ["EFFECT_IMAGE_IS_NOT_PRODUCTION_FILE"]
    if mock_used:
        warnings.append("MOCK_OUTPUT_NOT_A_REAL_CMF_RENDER")
    if not qa_result.passed:
        warnings.append("VISUAL_QA_NOT_PASSED")
    generation_record = {
        "schema_version": "1.0",
        "artwork_sha256": artwork_sha256,
        "provider": next(
            (item["provider"] for item in reversed(attempts) if item.get("operation") == "image_generation" and item.get("success")),
            "",
        ),
        "provider_config": [
            {
                "name": item.get("name", ""),
                "type": item.get("type", item.get("provider_type", "")),
                "model": item.get("model", ""),
                "may_incur_cost": bool(item.get("may_incur_cost")),
            }
            for item in provider_config.get("providers", [])
            if isinstance(item, dict)
        ],
        "mock": mock_used,
        "production_file": False,
        "input_count": 1,
        "max_qa_retries": max_qa_retries,
    }
    retry_record = {
        "schema_version": "1.0",
        "attempts": attempts,
        "qa_retry_limit": max_qa_retries,
        "qa_retries_used": max(0, sum(item.get("stage") == "visual_qa_decision" for item in attempts) - 1),
        "final_action": qa_result.recommended_action,
    }
    review_checklist = "\n".join(
        [
            "# CMF Visual Review Checklist",
            "",
            "- [ ] 核对 Logo、中文、产品名、主视觉、颜色和版式未被重绘或移动。",
            "- [ ] 核对结构、比例、正反侧面映射和包装数量正确。",
            "- [ ] 确认刀模线、压痕线、安全区、工艺标注框未进入成品图。",
            "- [ ] 确认工艺仅附着在指定表面，反光方向合理且没有浮空、发光或溢出。",
            "- [ ] 软包装、热封边、瓶体和标签按真实结构复核。",
            "- [ ] 本效果图不得作为生产文件、打样结果或合规证明。",
            "",
        ]
    )
    return MockupGeneration(
        final_image,
        mime_type,
        cmf_plan,
        generation_record,
        qa_result,
        retry_record,
        review_checklist,
        tuple(warnings),
        status,
    )


def write_mockup_outputs(generation: MockupGeneration, output_dir: str | Path) -> list[Path]:
    """Write Module C outputs without applying local image effects or transformations."""
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    paths = [
        target / "mockup.png",
        target / "cmf-plan.json",
        target / "generation-record.json",
        target / "visual-qa.json",
        target / "retry-record.json",
        target / "review-checklist.md",
    ]
    paths[0].write_bytes(generation.image_bytes)
    paths[1].write_text(json.dumps(generation.cmf_plan, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths[2].write_text(json.dumps(generation.generation_record, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths[3].write_text(json.dumps(asdict(generation.visual_qa), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths[4].write_text(json.dumps(generation.retry_record, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths[5].write_text(generation.review_checklist, encoding="utf-8")
    return paths
