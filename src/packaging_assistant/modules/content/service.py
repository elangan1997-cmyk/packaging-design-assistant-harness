from __future__ import annotations

import json
import textwrap
import xml.etree.ElementTree as ET
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from packaging_assistant.exceptions import RequestValidationError
from packaging_assistant.models import PackagingContentSpec, PanelDefinition
from packaging_assistant.modules.content.fields import build_content_fields
from packaging_assistant.modules.content.models import ContentLayoutGeneration


SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
ET.register_namespace("", SVG_NS)
ET.register_namespace("inkscape", INKSCAPE_NS)

PROTECTED_LAYERS = ("LAYER_CUT", "LAYER_CREASE", "LAYER_BLEED", "LAYER_SAFE")
PANEL_ID_MAP = {
    "panel-front": ("panel-front", "front"),
    "panel-back": ("panel-back", "back"),
    "panel-left": ("panel-left", "left"),
    "panel-right": ("panel-right", "right"),
    "panel-glue": ("panel-glue", "glue"),
    "PANEL_FRONT": ("panel-front", "front"),
    "PANEL_BACK": ("panel-back", "back"),
    "PANEL_SIDE_LEFT": ("panel-left", "left"),
    "PANEL_SIDE_RIGHT": ("panel-right", "right"),
    "PANEL_GLUE": ("panel-glue", "glue"),
}


def _find_by_id(root: ET.Element, element_id: str) -> ET.Element | None:
    return next((item for item in root.iter() if item.attrib.get("id") == element_id), None)


def _load_brief(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, (str, Path)):
        path = Path(value).expanduser()
        if not path.is_file():
            raise RequestValidationError("INPUT_NOT_FOUND", f"产品资料不存在：{path}", {"path": str(path)})
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RequestValidationError("INVALID_BRIEF", "产品资料必须是合法 JSON。") from exc
        if isinstance(payload, dict):
            return payload
    raise RequestValidationError("INVALID_BRIEF", "brief 必须是 JSON 对象或 JSON 文件路径。")


def _parse_template(path_value: object) -> tuple[Path, ET.Element]:
    if not isinstance(path_value, (str, Path)):
        raise RequestValidationError("INVALID_TEMPLATE", "template 必须是 SVG 文件路径。")
    path = Path(path_value).expanduser()
    if not path.is_file():
        raise RequestValidationError("INPUT_NOT_FOUND", f"SVG 模板不存在：{path}", {"path": str(path)})
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise RequestValidationError("INVALID_SVG", "SVG XML 无法解析。") from exc
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise RequestValidationError("INVALID_SVG", "输入文件缺少 SVG 根元素。")
    return path, root


def _panels(root: ET.Element) -> tuple[PanelDefinition, ...]:
    guides = _find_by_id(root, "LAYER_CONTENT_GUIDES")
    if guides is None:
        raise RequestValidationError("MISSING_TEMPLATE_LAYER", "SVG 缺少 LAYER_CONTENT_GUIDES。")
    panels: list[PanelDefinition] = []
    for item in guides.iter():
        source_id = item.attrib.get("id", "")
        if source_id not in PANEL_ID_MAP or item.tag.rsplit("}", 1)[-1] != "rect":
            continue
        panel_id, role = PANEL_ID_MAP[source_id]
        try:
            panels.append(
                PanelDefinition(
                    panel_id=panel_id,
                    role=role,
                    x=float(item.attrib["x"]),
                    y=float(item.attrib["y"]),
                    width=float(item.attrib["width"]),
                    height=float(item.attrib["height"]),
                )
            )
        except (KeyError, ValueError) as exc:
            raise RequestValidationError("INVALID_PANEL_GUIDE", f"面板坐标无效：{source_id}") from exc
    usable = [panel for panel in panels if panel.role != "glue"]
    if not usable:
        raise RequestValidationError("MISSING_PANEL_GUIDES", "未找到可写入内容的语义面板。")
    return tuple(panels)


def _wrap(value: str, max_chars: int) -> list[str]:
    return textwrap.wrap(
        value,
        width=max(8, max_chars),
        break_long_words=True,
        break_on_hyphens=False,
        replace_whitespace=False,
    ) or [""]


def _protected_fingerprints(root: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for layer_id in PROTECTED_LAYERS:
        layer = _find_by_id(root, layer_id)
        if layer is None:
            raise RequestValidationError("MISSING_TEMPLATE_LAYER", f"SVG 缺少 {layer_id}。")
        result[layer_id] = ET.tostring(layer, encoding="unicode")
    return result


def _render_content(
    root: ET.Element,
    fields: tuple,
    panels: tuple[PanelDefinition, ...],
    safe_margin: float,
) -> tuple[tuple, list[dict[str, object]]]:
    artwork = _find_by_id(root, "LAYER_ARTWORK")
    if artwork is None:
        raise RequestValidationError("MISSING_TEMPLATE_LAYER", "SVG 缺少 LAYER_ARTWORK。")
    if any(item.attrib.get("id", "").startswith("field-") for item in root.iter()):
        raise RequestValidationError("CONTENT_ALREADY_PRESENT", "SVG 已包含内容字段；当前版本不会静默覆盖。")

    available = {panel.panel_id: panel for panel in panels if panel.role != "glue"}
    cursors = {panel_id: panel.y + safe_margin + 2.8 for panel_id, panel in available.items()}
    font_size = 2.8
    line_height = 4.2
    gap = 1.2
    placed_fields = []
    placements: list[dict[str, object]] = []

    for field in fields:
        candidates = [field.panel] + [key for key in ("panel-back", "panel-left", "panel-right", "panel-front") if key != field.panel]
        selected: tuple[PanelDefinition, list[str], float] | None = None
        for panel_id in candidates:
            panel = available.get(panel_id)
            if panel is None:
                continue
            usable_width = max(1.0, panel.width - 2 * safe_margin)
            lines = _wrap(field.value, int(usable_width / (font_size * 0.62)))
            last_baseline = cursors[panel_id] + (len(lines) - 1) * line_height
            if last_baseline <= panel.y + panel.height - safe_margin:
                selected = (panel, lines, last_baseline)
                break
        if selected is None:
            raise RequestValidationError(
                "CONTENT_OVERFLOW",
                f"字段内容无法放入安全区：{field.field_id}",
                {"field": field.field_id},
            )

        panel, lines, last_baseline = selected
        x = panel.x + safe_margin
        y = cursors[panel.panel_id]
        group = ET.SubElement(
            artwork,
            f"{{{SVG_NS}}}g",
            {
                "id": field.field_id,
                "data-field-type": field.field_type,
                "data-source": field.source.type,
                "data-source-reference": field.source.reference,
                "data-status": field.status,
                "data-panel": panel.panel_id,
                "data-layout-box": f"{panel.x},{panel.y},{panel.width},{panel.height}",
            },
        )
        text = ET.SubElement(
            group,
            f"{{{SVG_NS}}}text",
            {
                "x": f"{x:.4f}".rstrip("0").rstrip("."),
                "y": f"{y:.4f}".rstrip("0").rstrip("."),
                "font-family": "sans-serif",
                "font-size": str(font_size),
                "fill": "#111111",
            },
        )
        for index, line in enumerate(lines):
            tspan = ET.SubElement(
                text,
                f"{{{SVG_NS}}}tspan",
                {
                    "x": f"{x:.4f}".rstrip("0").rstrip("."),
                    "dy": "0" if index == 0 else str(line_height),
                },
            )
            tspan.text = line
        cursors[panel.panel_id] = last_baseline + line_height + gap
        placed = replace(field, panel=panel.panel_id)
        placed_fields.append(placed)
        placements.append(
            {
                "field_id": field.field_id,
                "panel": panel.panel_id,
                "x": x,
                "first_baseline_y": y,
                "last_baseline_y": last_baseline,
                "line_count": len(lines),
                "within_safe_area": True,
            }
        )
    return tuple(placed_fields), placements


def _source_report(spec: PackagingContentSpec) -> str:
    provided = [field for field in spec.fields if field.status == "user_provided"]
    lines = [
        "# Source Report",
        "",
        "本次内容仅使用用户提供的产品资料和 Harness 的缺失占位规则；未执行外部法规检索。",
        "",
        "## User-provided fields",
        "",
    ]
    lines.extend(
        f"- `{field.field_id}` ← `{field.source.reference}`" for field in provided
    )
    if not provided:
        lines.append("- 无")
    lines.extend(
        [
            "",
            "## Compliance boundary",
            "",
            "- 本报告不是法律审核或上市许可。",
            "- 执行标准、许可证、企业信息、声明和功效必须由用户及有资质人员复核。",
            "- 未提供的数据保留占位符，不作推测或补写。",
            "",
        ]
    )
    return "\n".join(lines)


def _missing_report(spec: PackagingContentSpec) -> str:
    missing = [field for field in spec.fields if field.status == "missing"]
    lines = ["# Missing Fields", "", f"共 {len(missing)} 项待提供或待确认。", ""]
    lines.extend(f"- `{field.field_id}`：{field.value}" for field in missing)
    lines.append("")
    return "\n".join(lines)


def _review_checklist(spec: PackagingContentSpec) -> str:
    return "\n".join(
        [
            "# Review Checklist",
            "",
            "- [ ] 核对品牌名、产品名、规格和净含量是否与正式资料一致。",
            "- [ ] 核对生产企业、地址、联系方式是否真实完整。",
            "- [ ] 由有资质人员确认执行标准、许可证和认证适用性。",
            "- [ ] 审核功效、警示、使用方法和贮存表述。",
            "- [ ] 由设计人员检查字号、可读性、条码净空区和最终面板排版。",
            "- [ ] 确认文字未进入糊口、刀线、压痕线或安全区之外。",
            "- [ ] 印前输出前完成转曲、出血、分色和供应商复核。",
            "",
            f"字段总数：{len(spec.fields)}；待补充：{sum(field.status == 'missing' for field in spec.fields)}。",
            "",
        ]
    )


def generate_content_layout(parameters: dict[str, Any]) -> ContentLayoutGeneration:
    """Write sourced packaging fields into an SVG artwork layer without touching structure layers."""
    _, root = _parse_template(parameters.get("template"))
    brief = _load_brief(parameters.get("brief"))
    panels = _panels(root)
    before = _protected_fingerprints(root)
    try:
        safe_margin = float(parameters.get("safe_margin", 3.0))
    except (TypeError, ValueError) as exc:
        raise RequestValidationError("INVALID_PARAMETER", "safe_margin 必须是数字。") from exc
    if safe_margin <= 0:
        raise RequestValidationError("INVALID_PARAMETER", "safe_margin 必须大于 0。")

    fields = build_content_fields(brief)
    placed_fields, placements = _render_content(root, fields, panels, safe_margin)
    jurisdiction = str(brief.get("jurisdiction", "CN") or "CN")
    product_category = str(brief.get("product_category", "") or "")
    spec = PackagingContentSpec(jurisdiction, product_category, placed_fields)

    content_metadata = ET.Element(f"{{{SVG_NS}}}metadata", {"id": "packaging-content-metadata"})
    content_metadata.text = json.dumps(
        {
            "schema_version": spec.schema_version,
            "jurisdiction": jurisdiction,
            "product_category": product_category,
            "field_count": len(placed_fields),
            "manual_review_required": True,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    root.insert(2, content_metadata)
    after = _protected_fingerprints(root)
    protected_unchanged = before == after
    ids = [item.attrib["id"] for item in root.iter() if "id" in item.attrib]
    unique_ids = len(ids) == len(set(ids))
    no_glue_fields = all(field.panel != "panel-glue" for field in placed_fields)
    if not (protected_unchanged and unique_ids and no_glue_fields):
        raise RequestValidationError("CONTENT_VALIDATION_FAILED", "内容写入后的结构保护校验失败。")

    ET.indent(root, space="  ")
    svg = ET.tostring(root, encoding="unicode", xml_declaration=True)
    missing_count = sum(field.status == "missing" for field in placed_fields)
    validation = {
        "valid": True,
        "checks": {
            "svg_xml_valid": True,
            "protected_layers_unchanged": protected_unchanged,
            "unique_ids": unique_ids,
            "all_fields_have_source": all(bool(field.source.type) for field in placed_fields),
            "all_fields_have_status": all(bool(field.status) for field in placed_fields),
            "all_fields_within_safe_area": all(item["within_safe_area"] for item in placements),
            "no_fields_in_glue_panel": no_glue_fields,
        },
        "counts": {
            "fields": len(placed_fields),
            "missing_fields": missing_count,
            "panels": len(panels),
        },
        "placements": placements,
        "warnings": ["REQUIRES_COMPLIANCE_REVIEW"] + (["MISSING_CONTENT_FIELDS"] if missing_count else []),
        "manual_review_required": True,
    }
    return ContentLayoutGeneration(
        svg=svg,
        spec=spec,
        panels=panels,
        validation=validation,
        source_report=_source_report(spec),
        missing_fields_report=_missing_report(spec),
        review_checklist=_review_checklist(spec),
    )


def write_content_outputs(generation: ContentLayoutGeneration, directory: str | Path) -> list[Path]:
    target = Path(directory)
    outputs = (
        ("content-layout.svg", generation.svg),
        ("content-spec.json", json.dumps(asdict(generation.spec), ensure_ascii=False, indent=2, sort_keys=True) + "\n"),
        ("source-report.md", generation.source_report),
        ("missing-fields.md", generation.missing_fields_report),
        ("review-checklist.md", generation.review_checklist),
    )
    paths: list[Path] = []
    for name, content in outputs:
        path = target / name
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths
