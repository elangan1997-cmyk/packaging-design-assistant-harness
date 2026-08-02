from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from packaging_assistant.exceptions import RequestValidationError


MM_PER_UNIT = {"mm": 1.0, "cm": 10.0, "in": 25.4}


@dataclass(frozen=True)
class StructureModel:
    code: str
    name_zh: str
    aliases: tuple[str, ...]
    implemented: bool
    version: str = "box-v2.0"


@dataclass(frozen=True)
class StructureDimensions:
    length: float
    width: float
    height: float
    unit: str = "mm"
    dimension_type: str = "unspecified"

    @classmethod
    def from_dict(cls, data: object) -> "StructureDimensions":
        if not isinstance(data, dict):
            raise RequestValidationError(
                "INVALID_DIMENSIONS", "dimensions 必须是对象。", {"field": "dimensions"}
            )
        missing = [key for key in ("length", "width", "height") if key not in data]
        if missing:
            raise RequestValidationError(
                "MISSING_REQUIRED_FIELD", "缺少结构尺寸。", {"missing_fields": missing}
            )
        unit = str(data.get("unit", "mm")).lower()
        if unit not in MM_PER_UNIT:
            raise RequestValidationError(
                "UNSUPPORTED_UNIT", f"不支持的尺寸单位：{unit}", {"supported_units": sorted(MM_PER_UNIT)}
            )
        try:
            scale = MM_PER_UNIT[unit]
            length = float(data["length"]) * scale
            width = float(data["width"]) * scale
            height = float(data["height"]) * scale
        except (TypeError, ValueError) as exc:
            raise RequestValidationError(
                "INVALID_DIMENSIONS", "长、宽、高必须是数字。", {"field": "dimensions"}
            ) from exc
        if min(length, width, height) <= 0:
            raise RequestValidationError(
                "INVALID_DIMENSIONS", "长、宽、高必须大于 0。", {"field": "dimensions"}
            )
        return cls(
            length=length,
            width=width,
            height=height,
            unit="mm",
            dimension_type=str(data.get("dimension_type", "unspecified")),
        )


@dataclass(frozen=True)
class StructureSpec:
    model_code: str
    dimensions: StructureDimensions
    shrink: float = 0.5
    tuck_height: float = 12.0
    glue_width: float = 11.0
    bleed: float = 3.0
    safe_margin: float = 3.0
    output_mode: str = "DESIGN_TEMPLATE"
    model_version: str = "box-v2.0-lock-bottom-1.0"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StructureSpec":
        dimensions = StructureDimensions.from_dict(data.get("dimensions"))
        values: dict[str, float] = {}
        for key, default in (
            ("shrink", 0.5),
            ("tuck_height", 12.0),
            ("glue_width", 11.0),
            ("bleed", 3.0),
            ("safe_margin", 3.0),
        ):
            try:
                values[key] = float(data.get(key, default))
            except (TypeError, ValueError) as exc:
                raise RequestValidationError(
                    "INVALID_PARAMETER", f"{key} 必须是数字。", {"field": key}
                ) from exc
        if values["shrink"] < 0 or min(values["tuck_height"], values["glue_width"]) <= 0:
            raise RequestValidationError(
                "INVALID_PARAMETER", "缩位不能为负；插舌高度和粘口宽度必须大于 0。"
            )
        return cls(
            model_code=str(data.get("model_code", "")),
            dimensions=dimensions,
            shrink=values["shrink"],
            tuck_height=values["tuck_height"],
            glue_width=values["glue_width"],
            bleed=values["bleed"],
            safe_margin=values["safe_margin"],
            output_mode=str(data.get("output_mode", "DESIGN_TEMPLATE")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Primitive:
    kind: str
    element_id: str
    values: tuple[float, ...]
    commands: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Panel:
    panel_id: str
    name: str
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class StructureGeometry:
    cut: tuple[Primitive, ...]
    crease: tuple[Primitive, ...]
    panels: tuple[Panel, ...]
    bounds: tuple[float, float, float, float]


@dataclass(frozen=True)
class StructureGeneration:
    spec: dict[str, Any]
    validation: dict[str, Any]
    svg: str
    geometry: StructureGeometry

