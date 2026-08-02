from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from packaging_assistant.models import ContentField, ContentSource


@dataclass(frozen=True)
class FieldRule:
    field_id: str
    field_type: str
    path: tuple[str, ...]
    placeholder: str
    panel: str
    prefix: str = ""


FIELD_RULES: tuple[FieldRule, ...] = (
    FieldRule("field-brand-name", "brand-name", ("brand", "name"), "[待提供：品牌名称]", "panel-front"),
    FieldRule("field-brand-slogan", "brand-slogan", ("brand", "slogan"), "[待提供：品牌口号]", "panel-front"),
    FieldRule("field-product-name", "product-name", ("product", "name"), "[待提供：产品名称]", "panel-front"),
    FieldRule("field-product-variant", "product-variant", ("product", "variant"), "[待提供：产品规格/型号]", "panel-front"),
    FieldRule("field-product-description", "product-description", ("product", "description"), "[待提供：产品描述]", "panel-back"),
    FieldRule("field-selling-points", "selling-points", ("product", "selling_points"), "[待提供：产品卖点]", "panel-right"),
    FieldRule("field-net-content", "net-content", ("product", "net_content"), "[待提供：净含量]", "panel-front", "净含量："),
    FieldRule("field-specification", "specification", ("product", "specification"), "[待提供：规格]", "panel-left", "规格："),
    FieldRule("field-ingredients", "ingredients", ("product", "ingredients"), "[待提供：成分/配料]", "panel-back", "成分/配料："),
    FieldRule("field-materials", "materials", ("product", "materials"), "[待提供：材料信息]", "panel-back", "材料："),
    FieldRule("field-directions", "directions", ("product", "directions"), "[待提供：使用方法]", "panel-back", "使用方法："),
    FieldRule("field-warnings", "warnings", ("product", "warnings"), "[待提供：警示语]", "panel-back", "警示："),
    FieldRule("field-storage", "storage", ("product", "storage"), "[待提供：贮存条件]", "panel-back", "贮存："),
    FieldRule("field-manufacturer", "manufacturer", ("business", "manufacturer"), "[待提供：生产企业名称]", "panel-back", "生产企业："),
    FieldRule("field-address", "address", ("business", "address"), "[待提供：生产地址]", "panel-back", "地址："),
    FieldRule("field-contact", "contact", ("business", "contact"), "[待提供：联系方式]", "panel-back", "联系方式："),
    FieldRule("field-website", "website", ("business", "website"), "[待提供：网站]", "panel-right", "网站："),
    FieldRule("field-execution-standard", "execution-standard", ("standards", "execution_standard"), "[待确认：执行标准]", "panel-left", "执行标准："),
    FieldRule("field-license-number", "license-number", ("standards", "license_number"), "[待确认：许可证编号]", "panel-left", "许可证编号："),
    FieldRule("field-certifications", "certifications", ("standards", "certifications"), "[待确认：认证信息]", "panel-left", "认证："),
    FieldRule("field-barcode-placeholder", "barcode-placeholder", ("product", "barcode"), "[待生成或粘贴：商品条码]", "panel-back"),
)


def _lookup(data: dict[str, Any], path: tuple[str, ...]) -> object:
    current: object = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _text(value: object) -> str:
    if isinstance(value, list):
        return "、".join(str(item).strip() for item in value if str(item).strip())
    if value is None:
        return ""
    return str(value).strip()


def build_content_fields(brief: dict[str, Any]) -> tuple[ContentField, ...]:
    """Map user-supplied facts to fields without inventing regulated information."""
    fields: list[ContentField] = []
    for rule in FIELD_RULES:
        raw = _text(_lookup(brief, rule.path))
        if raw:
            value = f"{rule.prefix}{raw}"
            status = "user_provided"
            source = ContentSource("user_input", ".".join(rule.path))
        else:
            value = rule.placeholder
            status = "missing"
            source = ContentSource("missing", "")
        fields.append(
            ContentField(
                field_id=rule.field_id,
                field_type=rule.field_type,
                value=value,
                status=status,
                source=source,
                panel=rule.panel,
            )
        )
    fields.append(
        ContentField(
            field_id="field-review-note",
            field_type="review-note",
            value="包装信息草稿；法规、声明和企业信息须人工复核。",
            status="review_required",
            source=ContentSource("system_rule", "REQUIRES_COMPLIANCE_REVIEW"),
            panel="panel-right",
        )
    )
    return tuple(fields)
