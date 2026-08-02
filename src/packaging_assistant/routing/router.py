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


def _infer_route(request: PackagingRequest) -> RouteDecision:
    """Infer a high-level workflow from explicit facts and classified assets."""
    parameters = request.parameters
    assets = inspect_assets(_asset_values(parameters))
    goal = str(parameters.get("user_goal", parameters.get("goal", ""))).strip()
    normalized_goal = goal.lower()
    available: list[str] = []
    if parameters.get("model_code"):
        available.append("model_code")
    if parameters.get("dimensions"):
        available.append("dimensions")
    if parameters.get("brief") or parameters.get("product_data"):
        available.append("product_data")
    available.extend(f"asset:{asset.role}" for asset in assets)
    evidence = list(available)
    blank = any(asset.role == "blank_structure_template" for asset in assets)
    completed = any(asset.role == "completed_artwork" for asset in assets)
    stages = parameters.get("stages", [])
    stage_names = (
        {str(item) for item in stages if isinstance(item, (str, int, float))}
        if isinstance(stages, list)
        else set()
    )
    multi = bool(parameters.get("from_dimensions_to_mockup")) or (
        {"structure_template", "content_layout", "mockup_render"}.issubset(stage_names)
    )
    wants_mockup = bool(parameters.get("wants_mockup")) or any(
        token in normalized_goal for token in ("效果图", "mockup", "cmf", "材质", "工艺")
    )
    wants_content = bool(parameters.get("wants_content")) or any(
        token in normalized_goal for token in ("包装信息", "背标", "文案", "排版", "content")
    )
    wants_structure = bool(parameters.get("wants_structure")) or any(
        token in normalized_goal for token in ("刀模", "结构模板", "dieline", "svg模板")
    )

    if multi:
        return RouteDecision(
            action="multi_stage_workflow",
            route="multi_stage_workflow",
            module="orchestrator",
            implemented=True,
            reason="explicit_multi_stage_goal",
            input_assets=assets,
            providers=["image_generation", "vision"],
            may_incur_cost=True,
            expected_outputs=["template.svg", "content-layout.svg", "mockup.png", "visual-qa.json"],
            manual_review_items=["每个阶段独立校验；效果图不能替代生产文件"],
            confidence=1.0,
            user_goal=goal,
            available_inputs=available,
            next_action="structure_template",
            evidence=[*evidence, "explicit:multi_stage"],
        )
    if wants_mockup and blank:
        return RouteDecision(
            action="clarification_required",
            route="clarification_required",
            module="routing",
            implemented=True,
            reason="blank_dieline_conflicts_with_mockup_request",
            missing_fields=["completed_artwork"],
            input_assets=assets,
            confidence=1.0,
            user_goal=goal,
            available_inputs=available,
            next_action="request_completed_artwork",
            needs_clarification=True,
            clarification_question="当前是空白刀模，请提供已完成图文设计的包装稿。",
            evidence=[*evidence, "conflict:blank_dieline_vs_mockup"],
        )
    if wants_mockup or (completed and bool(parameters.get("dimensions"))):
        missing = []
        if not completed:
            missing.append("completed_artwork")
        if not parameters.get("dimensions"):
            missing.append("dimensions")
        return RouteDecision(
            action="mockup_render",
            route="mockup_render",
            module="mockup",
            implemented=True,
            reason="completed_artwork_or_cmf_goal",
            missing_fields=missing,
            input_assets=assets,
            providers=["image_generation", "vision"],
            may_incur_cost=True,
            expected_outputs=list(ACTIONS["mockup_render"]["outputs"]),
            manual_review_items=["确认费用和 Provider；效果图必须经过视觉 QA 与人工复核"],
            confidence=0.98 if completed else 0.82,
            user_goal=goal,
            available_inputs=available,
            next_action="mockup_render" if not missing else "request_missing_input",
            needs_clarification=bool(missing),
            clarification_question="请提供完成设计稿和真实包装尺寸。" if missing else None,
            evidence=[*evidence, "intent:mockup"],
        )
    if wants_content or (blank and (parameters.get("brief") or parameters.get("product_data"))):
        missing = []
        if not blank:
            missing.append("blank_structure_template")
        if not (parameters.get("brief") or parameters.get("product_data")):
            missing.append("product_data")
        return RouteDecision(
            action="content_layout",
            route="content_layout",
            module="content",
            implemented=True,
            reason="blank_template_and_product_data",
            missing_fields=missing,
            input_assets=assets,
            expected_outputs=list(ACTIONS["content_layout"]["outputs"]),
            manual_review_items=["法规字段与来源必须由有资质人员复核"],
            confidence=0.98 if blank and not missing else 0.8,
            user_goal=goal,
            available_inputs=available,
            next_action="content_layout" if not missing else "request_missing_input",
            needs_clarification=bool(missing),
            clarification_question="请提供空白结构模板和产品资料。" if missing else None,
            evidence=[*evidence, "intent:content"],
        )
    if wants_structure or (parameters.get("model_code") and parameters.get("dimensions")):
        missing = [key for key in ("model_code", "dimensions") if not parameters.get(key)]
        return RouteDecision(
            action="structure_template",
            route="structure_template",
            module="structure",
            implemented=True,
            reason="box_model_and_dimensions",
            missing_fields=missing,
            input_assets=assets,
            expected_outputs=list(ACTIONS["structure_template"]["outputs"]),
            manual_review_items=["印厂必须复核结构与公差"],
            confidence=0.99 if not missing else 0.8,
            user_goal=goal,
            available_inputs=available,
            next_action="structure_template" if not missing else "request_missing_input",
            needs_clarification=bool(missing),
            clarification_question="请提供盒型和成品尺寸。" if missing else None,
            evidence=[*evidence, "intent:structure"],
        )
    return RouteDecision(
        action="clarification_required",
        route="clarification_required",
        module="routing",
        implemented=True,
        reason="insufficient_or_ambiguous_evidence",
        missing_fields=["user_goal"],
        input_assets=assets,
        confidence=0.0,
        user_goal=goal,
        available_inputs=available,
        next_action="ask_user_goal",
        needs_clarification=True,
        clarification_question="你希望生成刀模模板、编排包装信息，还是制作 CMF 效果图？",
        evidence=evidence or ["no_decisive_evidence"],
    )


def route_request(request: PackagingRequest) -> RouteDecision:
    if request.action == "route":
        return _infer_route(request)
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
            reason = {
                "carton.box_v2.mailer": "原脚本飞机盒样本实际为锁底盒结构，已拒绝作为飞机盒基准。",
                "carton.box_v2.custom": "“其它”没有固定参数化结构，需要用户提供自定义结构定义。",
            }.get(model.code, f"盒型“{model.name_zh}”尚未完成独立几何回归。")
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
        route=request.action,
        confidence=1.0 if not missing else 0.9,
        user_goal=str(request.parameters.get("user_goal", "")),
        available_inputs=[key for key, value in request.parameters.items() if value not in (None, "", [], {})],
        next_action=request.action if not missing else "request_missing_input",
        needs_clarification=bool(missing),
        clarification_question=(choice_prompt or {}).get("message") if missing else None,
        evidence=[f"explicit_action:{request.action}", *[f"asset:{asset.role}" for asset in assets]],
    )


def route_dict(request: PackagingRequest) -> dict[str, object]:
    return asdict(route_request(request))
