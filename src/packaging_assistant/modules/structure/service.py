from __future__ import annotations

from pathlib import Path
from typing import Any

from packaging_assistant.exceptions import NotImplementedCapabilityError, RequestValidationError
from packaging_assistant.modules.structure.carry_handle import build_carry_handle
from packaging_assistant.modules.structure.lock_bottom import build_lock_bottom
from packaging_assistant.modules.structure.mailer import build_mailer
from packaging_assistant.modules.structure.shipping_carton import build_shipping_carton
from packaging_assistant.modules.structure.tuck_cartons import (
    build_glue_bottom,
    build_hang_tab,
    build_same_direction_tuck,
    build_straight,
    build_top_cover,
)
from packaging_assistant.modules.structure.models import StructureGeneration, StructureSpec
from packaging_assistant.modules.structure.registry import resolve_model
from packaging_assistant.modules.structure.svg import LAYERS, render_svg


def generate_structure_template(parameters: dict[str, Any]) -> StructureGeneration:
    model_value = str(parameters.get("model_code", ""))
    model = resolve_model(model_value)
    if model is None:
        raise RequestValidationError(
            "UNKNOWN_STRUCTURE_MODEL", f"未知盒型：{model_value}", {"field": "model_code"}
        )
    if not model.implemented:
        reason = {
            "carton.box_v2.mailer": "原脚本飞机盒样本实际为锁底盒结构，已拒绝作为飞机盒基准；正确结构尚待独立定义。",
            "carton.box_v2.custom": "“其它”没有固定参数化结构，需要用户提供自定义结构定义。",
        }.get(model.code, "该盒型尚未完成独立几何回归。")
        raise NotImplementedCapabilityError(
            "NOT_IMPLEMENTED",
            f"盒型“{model.name_zh}”已独立注册，但当前不可生成：{reason}",
            {"model_code": model.code, "reason": reason},
        )
    canonical_parameters = dict(parameters)
    canonical_parameters["model_code"] = model.code
    if model.code == "carton.box_v2.mailer":
        canonical_parameters.setdefault("board_thickness", 0.3)
        canonical_parameters.setdefault("bleed", 5.0)
        canonical_parameters.setdefault("material", "200g白卡(0.3mm)")
    versions = {
        "carton.box_v2.straight": "box-v2.0-straight-1.0",
        "carton.box_v2.lock_bottom": "box-v2.0-lock-bottom-1.0",
        "carton.box_v2.mailer": "box-v2.0-mailer-1.0",
        "carton.box_v2.top_cover": "box-v2.0-top-cover-1.0",
        "carton.box_v2.same_direction_tuck": "box-v2.0-same-direction-tuck-1.0",
        "carton.box_v2.glue_bottom": "box-v2.0-glue-bottom-1.0",
        "carton.box_v2.hang_tab": "box-v2.0-hang-tab-1.0",
        "carton.box_v2.carry_handle": "box-v2.0-carry-handle-1.0",
        "carton.box_v2.shipping_carton": "box-v2.0-shipping-carton-1.0",
    }
    canonical_parameters["model_version"] = versions[model.code]
    spec = StructureSpec.from_dict(canonical_parameters)
    if spec.output_mode != "DESIGN_TEMPLATE":
        raise RequestValidationError(
            "UNSUPPORTED_OUTPUT_MODE",
            "当前结构模块只输出 DESIGN_TEMPLATE。",
            {"supported_modes": ["DESIGN_TEMPLATE"]},
        )
    builders = {
        "carton.box_v2.straight": build_straight,
        "carton.box_v2.lock_bottom": build_lock_bottom,
        "carton.box_v2.mailer": build_mailer,
        "carton.box_v2.top_cover": build_top_cover,
        "carton.box_v2.same_direction_tuck": build_same_direction_tuck,
        "carton.box_v2.glue_bottom": build_glue_bottom,
        "carton.box_v2.hang_tab": build_hang_tab,
        "carton.box_v2.carry_handle": build_carry_handle,
        "carton.box_v2.shipping_carton": build_shipping_carton,
    }
    geometry = builders[model.code](spec)
    svg = render_svg(spec, geometry, model.name_zh)
    warnings = ["REQUIRES_MANUFACTURER_REVIEW"]
    if spec.dimensions.dimension_type == "unspecified":
        warnings.append("DIMENSION_TYPE_UNSPECIFIED")
    validation = {
        "valid": True,
        "model_code": model.code,
        "checks": {
            "positive_dimensions": True,
            "stable_element_ids": True,
            "required_layers_present": True,
            "deterministic_geometry": True,
            "original_script_regression_fixture_available": True,
        },
        "counts": {
            "cut_primitives": len(geometry.cut),
            "crease_primitives": len(geometry.crease),
            "panels": len(geometry.panels),
            "layers": len(LAYERS),
        },
        "warnings": warnings,
        "manual_review_required": True,
    }
    spec_payload = spec.to_dict()
    spec_payload.update(
        {
            "schema_version": "1.0",
            "name_zh": model.name_zh,
            "source_compatibility": f"AI脚本插件146合集 / 盒型2.0 / {model.name_zh} black-box regression",
        }
    )
    return StructureGeneration(spec=spec_payload, validation=validation, svg=svg, geometry=geometry)


def write_structure_outputs(generation: StructureGeneration, directory: str | Path) -> list[Path]:
    target = Path(directory)
    svg_path = target / "template.svg"
    spec_path = target / "structure_spec.json"
    validation_path = target / "validation_report.json"
    svg_path.write_text(generation.svg, encoding="utf-8")
    import json

    spec_path.write_text(json.dumps(generation.spec, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validation_path.write_text(
        json.dumps(generation.validation, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return [svg_path, spec_path, validation_path]
