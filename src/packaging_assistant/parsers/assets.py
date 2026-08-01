from __future__ import annotations

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
    if path.exists() and path.is_file():
        metadata["size_bytes"] = path.stat().st_size
        if kind == AssetKind.SVG.value:
            head = path.read_text(encoding="utf-8", errors="replace")[:4096].lower()
            metadata.update(
                {
                    "has_dieline": any(token in head for token in ("layer_cut", "cut", "crease")),
                    "has_structure_metadata": "<metadata" in head,
                    "has_artwork": any(token in head for token in ("<image", "layer_artwork", "artwork")),
                }
            )
    return PackagingAsset(path=str(path), type=kind, exists=path.exists(), metadata=metadata)


def inspect_assets(values: Iterable[str | Path]) -> list[PackagingAsset]:
    return [inspect_asset(value) for value in values]

