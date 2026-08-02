from __future__ import annotations

import html
import json
from typing import Iterable

from packaging_assistant.modules.structure.models import Primitive, StructureGeometry, StructureSpec


LAYERS = (
    "LAYER_CUT",
    "LAYER_CREASE",
    "LAYER_BLEED",
    "LAYER_SAFE",
    "LAYER_PANEL_LABELS",
    "LAYER_DIMENSIONS",
    "LAYER_ARTWORK",
    "LAYER_CONTENT_GUIDES",
    "LAYER_REVIEW_NOTES",
    "LAYER_NOTES",
)


def _n(value: float) -> str:
    rounded = round(value, 4)
    if abs(rounded) < 0.00005:
        rounded = 0.0
    return f"{rounded:.4f}".rstrip("0").rstrip(".")


def _points(values: tuple[float, ...]) -> str:
    return " ".join(f"{_n(values[index])},{_n(values[index + 1])}" for index in range(0, len(values), 2))


def _path_d(primitive: Primitive) -> str:
    values = iter(primitive.values)
    chunks: list[str] = []
    sizes = {"M": 2, "L": 2, "C": 6, "H": 1, "c": 6, "h": 1, "l": 2, "v": 1, "z": 0}
    for command in primitive.commands:
        size = sizes[command]
        numbers = [_n(next(values)) for _ in range(size)]
        chunks.append(command + " ".join(numbers))
    return " ".join(chunks)


def _primitive_xml(primitive: Primitive, css_class: str) -> str:
    attrs = f'id="{primitive.element_id}" class="{css_class}" data-kind="{primitive.kind}"'
    if primitive.kind == "line":
        x1, y1, x2, y2 = primitive.values
        return f'<line {attrs} x1="{_n(x1)}" y1="{_n(y1)}" x2="{_n(x2)}" y2="{_n(y2)}" />'
    if primitive.kind == "polyline":
        return f'<polyline {attrs} points="{_points(primitive.values)}" />'
    return f'<path {attrs} data-commands="{" ".join(primitive.commands)}" d="{_path_d(primitive)}" />'


def _layer(layer_id: str, content: Iterable[str] = ()) -> str:
    body = "\n    ".join(content)
    if body:
        return f'  <g id="{layer_id}" inkscape:groupmode="layer" inkscape:label="{layer_id}">\n    {body}\n  </g>'
    return f'  <g id="{layer_id}" inkscape:groupmode="layer" inkscape:label="{layer_id}" />'


def render_svg(spec: StructureSpec, geometry: StructureGeometry, model_name: str) -> str:
    min_x, min_y, max_x, max_y = geometry.bounds
    margin = max(5.0, spec.bleed + 2.0)
    view_x = min_x - margin
    view_y = min_y - margin
    view_w = max_x - min_x + 2 * margin
    view_h = max_y - min_y + 2 * margin
    metadata = {
        "schema_version": "1.0",
        "model_code": spec.model_code,
        "model_version": spec.model_version,
        "dimensions_mm": {
            "length": spec.dimensions.length,
            "width": spec.dimensions.width,
            "height": spec.dimensions.height,
        },
        "parameters_mm": {
            "shrink": spec.shrink,
            "tuck_height": spec.tuck_height,
            "glue_width": spec.glue_width,
            "bleed": spec.bleed,
            "safe_margin": spec.safe_margin,
        },
        "output_mode": spec.output_mode,
        "warning": "REQUIRES_MANUFACTURER_REVIEW",
    }
    panel_roles = {
        "panel-front": "front",
        "panel-back": "back",
        "panel-left": "left",
        "panel-right": "right",
        "panel-glue": "glue",
    }
    panel_rects = []
    for panel in geometry.panels:
        panel_type = "glue-flap" if panel.panel_id == "panel-glue" else "artwork-panel"
        panel_rects.append(
            f'<rect id="{panel.panel_id}" class="panel-guide" '
            f'x="{_n(panel.x)}" y="{_n(panel.y)}" '
            f'width="{_n(panel.width)}" height="{_n(panel.height)}" '
            f'data-panel-name="{html.escape(panel.name)}" '
            f'data-role="{panel_roles.get(panel.panel_id, "other")}" '
            f'data-panel-type="{panel_type}" />'
        )
    panel_labels = [
        f'<text id="LABEL_{panel.panel_id}" class="panel-label" x="{_n(panel.x + panel.width / 2)}" y="{_n(panel.y + panel.height / 2)}">{html.escape(panel.name)}</text>'
        for panel in geometry.panels
    ]
    layer_content = {
        "LAYER_CUT": [_primitive_xml(item, "cut") for item in geometry.cut],
        "LAYER_CREASE": [_primitive_xml(item, "crease") for item in geometry.crease],
        "LAYER_CONTENT_GUIDES": panel_rects,
        "LAYER_PANEL_LABELS": panel_labels,
        "LAYER_REVIEW_NOTES": [
            '<text id="NOTE_MANUFACTURER_REVIEW" class="review-note" x="0" y="0">DESIGN_TEMPLATE · REQUIRES_MANUFACTURER_REVIEW</text>'
        ],
    }
    layers = "\n".join(_layer(layer, layer_content.get(layer, ())) for layer in LAYERS)
    metadata_text = html.escape(json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="{_n(view_w)}mm" height="{_n(view_h)}mm" viewBox="{_n(view_x)} {_n(view_y)} {_n(view_w)} {_n(view_h)}">
  <title>Box 2.0 {html.escape(model_name)}结构设计模板</title>
  <metadata id="PACKAGING_STRUCTURE_METADATA">{metadata_text}</metadata>
  <style>
    .cut {{ fill: none; stroke: #000000; stroke-width: 0.1; vector-effect: non-scaling-stroke; }}
    .crease {{ fill: none; stroke: #e60012; stroke-width: 0.1; stroke-dasharray: 3 2; vector-effect: non-scaling-stroke; }}
    .panel-guide {{ fill: none; stroke: #00a0e9; stroke-width: 0.08; stroke-dasharray: 1 1; vector-effect: non-scaling-stroke; }}
    .panel-label {{ fill: #666666; font-family: sans-serif; font-size: 3px; text-anchor: middle; }}
    .review-note {{ fill: #c00000; font-family: sans-serif; font-size: 3px; }}
  </style>
{layers}
</svg>
'''
