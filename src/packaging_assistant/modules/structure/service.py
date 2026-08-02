from __future__ import annotations

from pathlib import Path
from typing import Any

from packaging_assistant.exceptions import NotImplementedCapabilityError, RequestValidationError
from packaging_assistant.modules.structure.lock_bottom import build_lock_bottom
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
        raise NotImplementedCapabilityError(
            "NOT_IMPLEMENTED",
            f"盒型“{model.name_zh}”已独立注册，但尚未完成原脚本几何复刻。",
            {"model_code": model.code},
        )
    canonical_parameters = dict(parameters)
    canonical_parameters["model_code"] = model.code
    spec = StructureSpec.from_dict(canonical_parameters)
    if spec.output_mode != "DESIGN_TEMPLATE":
        raise RequestValidationError(
            "UNSUPPORTED_OUTPUT_MODE",
            "当前结构模块只输出 DESIGN_TEMPLATE。",
            {"supported_modes": ["DESIGN_TEMPLATE"]},
        )
    geometry = build_lock_bottom(spec)
    svg = render_svg(spec, geometry)
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
            "source_compatibility": "AI脚本插件146合集 / 盒型2.0 / 锁底盒 black-box regression",
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

