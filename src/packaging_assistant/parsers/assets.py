from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

from packaging_assistant.models import AssetKind, PackagingAsset


EXTENSION_KINDS = {
    ".svg": AssetKind.SVG.value,
    ".png": AssetKind.IMAGE.value,
    ".jpg": AssetKind.IMAGE.value,
    ".jpeg": AssetKind.IMAGE.value,
    ".webp": AssetKind.IMAGE.value,
    ".pdf": AssetKind.PDF.value,
    ".json": AssetKind.JSON.value,
    ".yaml": AssetKind.YAML.value,
    ".yml": AssetKind.YAML.value,
    ".txt": AssetKind.TEXT.value,
    ".md": AssetKind.TEXT.value,
}


def inspect_asset(path_value: str | Path) -> PackagingAsset:
    path = Path(path_value).expanduser()
    kind = EXTENSION_KINDS.get(path.suffix.lower(), AssetKind.UNKNOWN.value)
    metadata: dict[str, object] = {"suffix": path.suffix.lower()}
    role = "input"
    if path.exists() and path.is_file():
        metadata["size_bytes"] = path.stat().st_size
        if kind == AssetKind.SVG.value:
            try:
                root = ET.parse(path).getroot()
                elements = list(root.iter())
                ids = [item.attrib.get("id", "") for item in elements]
                layer_artwork = next((item for item in elements if item.attrib.get("id") == "LAYER_ARTWORK"), None)
                has_content_fields = any(value.startswith("field-") for value in ids)
                has_artwork = bool(layer_artwork is not None and list(layer_artwork))
                has_dieline = "LAYER_CUT" in ids or "LAYER_CREASE" in ids
                has_panel_ids = any(value.startswith("panel-") or value.startswith("PANEL_") for value in ids)
                has_finish_layers = any(
                    token in value.lower() for value in ids for token in ("finish", "foil", "uv", "emboss")
                )
                tags = [item.tag.rsplit("}", 1)[-1] for item in elements]
                metadata.update(
                    {
                        "has_dieline": has_dieline,
                        "has_structure_metadata": any(tag == "metadata" for tag in tags),
                        "has_panel_ids": has_panel_ids,
                        "has_artwork": has_artwork,
                        "has_content_fields": has_content_fields,
                        "has_finish_layers": has_finish_layers,
                        "has_logo": any("logo" in value.lower() for value in ids),
                        "has_text_objects": "text" in tags,
                        "has_embedded_images": "image" in tags,
                        "is_blank_dieline": has_dieline and not has_artwork and not has_content_fields,
                    }
                )
                if metadata["is_blank_dieline"]:
                    role = "blank_structure_template"
                elif has_artwork or has_content_fields:
                    role = "completed_artwork"
                else:
                    role = "vector_artwork"
            except ET.ParseError:
                metadata["parse_error"] = "invalid_svg_xml"
        elif kind == AssetKind.JSON.value:
            role = "structured_data"
    return PackagingAsset(path=str(path), type=kind, role=role, exists=path.exists(), metadata=metadata)


def inspect_assets(values: Iterable[str | Path]) -> list[PackagingAsset]:
    return [inspect_asset(value) for value in values]
