from __future__ import annotations

from dataclasses import asdict

from packaging_assistant.capabilities import ACTIONS
from packaging_assistant.models import PackagingRequest, RouteDecision
from packaging_assistant.modules.structure import model_choices, resolve_model
from packaging_assistant.parsers import inspect_assets
from packaging_assistant.providers import load_provider_config


def _asset_values(parameters: dict[str, object]) -> list[str]:
    values: list[str] = []
    for key in ("input", "template", "artwork", "brief", "spec", "file"):
        value = parameters.get(key)
        if isinstance(value, str) and value:
            values.append(value)
    raw_assets = parameters.get("assets")
    if isinstance(raw_assets, list):
        values.extend(str(item) for item in raw_assets if isinstance(item, (str, int, float)))
    return values


def route_request(request: PackagingRequest) -> RouteDecision:
    capability = ACTIONS[request.action]
    missing: list[str] = []
    choice_prompt: dict[str, object] | None = None
    if request.action == "structure_template":
        if not request.parameters.get("model_code"):
            missing.append("model_code")
            choice_prompt = {
                "field": "model_code",
                "message": "请选择盒型",
                "options": model_choices(),
                "reply_hint": "回复盒型名称或对应序号，例如：锁底盒 或 1。",
            }
        if not request.parameters.get("dimensions"):
            missing.append("dimensions")
    elif request.action == "content_layout":
        if not request.parameters.get("template"):
            missing.append("template")
        if not request.parameters.get("brief"):
            missing.append("brief")
    elif request.action == "mockup_render":
        config = load_provider_config(request.parameters.get("config"))
        defaults = config.get("mockup", {}) if isinstance(config, dict) else {}
        effective = {**(defaults if isinstance(defaults, dict) else {}), **request.parameters}
        if not request.parameters.get("artwork"):
            missing.append("artwork")
        if not effective.get("dimensions"):
            missing.append("dimensions")
        if not effective.get("material"):
            missing.append("material")

    assets = inspect_assets(_asset_values(request.parameters))
    implemented = bool(capability["implemented"])
    reason = "capability_available" if implemented else str(capability.get("note", "not_implemented"))
    if request.action == "structure_template" and request.parameters.get("model_code"):
        model = resolve_model(str(request.parameters["model_code"]))
        if model is None:
            implemented = False
            reason = f"未知盒型：{request.parameters['model_code']}"
        elif not model.implemented:
            implemented = False
            reason = f"盒型“{model.name_zh}”已独立注册，但尚未完成原脚本几何复刻。"
        else:
            reason = f"model_available:{model.code}"
    if request.action == "mockup_render" and any(asset.role == "blank_structure_template" for asset in assets):
        if "completed_artwork" not in missing:
            missing.append("completed_artwork")
        reason = "blank_dieline_conflicts_with_mockup_request"
    manual_review = []
    if request.action == "structure_template":
        manual_review.append("印厂必须复核结构、公差、纸厚补偿和模切可生产性")
    if request.action == "content_layout":
        manual_review.append("法规字段与来源必须由有资质人员复核")
    if request.action == "mockup_render":
        manual_review.extend(
            [
                "确认外部 Provider、模型、费用和重试上限",
                "视觉 QA 与人工复核必须通过",
                "效果图不能替代打样或印刷文件",
            ]
        )

    return RouteDecision(
        action=request.action,
        module=str(capability["module"]),
        implemented=implemented,
        reason=reason,
        missing_fields=missing,
        input_assets=assets,
        providers=list(capability.get("providers", [])),
        may_incur_cost=bool(capability.get("providers")),
        expected_outputs=list(capability.get("outputs", [])),
        manual_review_items=manual_review,
        choice_prompt=choice_prompt,
    )


def route_dict(request: PackagingRequest) -> dict[str, object]:
    return asdict(route_request(request))
