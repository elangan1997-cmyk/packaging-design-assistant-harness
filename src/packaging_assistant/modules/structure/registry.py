from __future__ import annotations

from packaging_assistant.modules.structure.models import StructureModel


MODELS: tuple[StructureModel, ...] = (
    StructureModel("carton.box_v2.straight", "直线盒", ("直线盒", "直线", "straight"), True),
    StructureModel(
        "carton.box_v2.lock_bottom",
        "锁底盒",
        ("锁底盒", "锁底", "lock bottom", "lock-bottom", "auto lock bottom"),
        True,
    ),
    StructureModel("carton.box_v2.mailer", "飞机盒", ("飞机盒", "mailer"), False),
    StructureModel("carton.box_v2.top_cover", "上盖盒", ("上盖盒", "top cover"), True),
    StructureModel(
        "carton.box_v2.same_direction_tuck",
        "同向盖",
        ("同向盖", "同向插口", "same direction tuck"),
        True,
    ),
    StructureModel("carton.box_v2.glue_bottom", "粘底盒", ("粘底盒", "粘底", "glue bottom"), True),
    StructureModel("carton.box_v2.hang_tab", "挂耳盒", ("挂耳盒", "挂耳", "hang tab"), True),
    StructureModel("carton.box_v2.carry_handle", "手提盒", ("手提盒", "carry handle"), True),
    StructureModel("carton.box_v2.shipping_carton", "纸箱", ("纸箱", "shipping carton"), True),
    StructureModel("carton.box_v2.custom", "其它", ("其它", "其他", "custom"), False),
)


def _key(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").split())


def resolve_model(value: str) -> StructureModel | None:
    target = _key(value)
    for model in MODELS:
        if target == _key(model.code) or target == _key(model.name_zh):
            return model
        if target in {_key(alias) for alias in model.aliases}:
            return model
    return None


def model_report() -> list[dict[str, object]]:
    return [
        {
            "code": model.code,
            "name_zh": model.name_zh,
            "aliases": list(model.aliases),
            "implemented": model.implemented,
            "version": model.version,
        }
        for model in MODELS
    ]


def model_choices() -> list[dict[str, object]]:
    """Return conversational choices with available models first."""
    ordered = sorted(enumerate(MODELS), key=lambda item: (not item[1].implemented, item[0]))
    return [
        {
            "value": model.code,
            "label": model.name_zh,
            "status": "available" if model.implemented else "not_implemented",
        }
        for _, model in ordered
    ]
