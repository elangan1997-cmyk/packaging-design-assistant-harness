from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LegacyCMFAdapter:
    repository_root: Path

    def reference_paths(self) -> list[Path]:
        names = (
            "finish-taxonomy.md",
            "material-compatibility.md",
            "output-format.md",
            "prompt-templates.md",
        )
        return [self.repository_root / "references" / name for name in names]

    def capability(self) -> dict[str, object]:
        paths = self.reference_paths()
        return {
            "name": "legacy_cmf_advisory",
            "advisory_available": all(path.is_file() for path in paths),
            "rendering_available": False,
            "references": [str(path) for path in paths],
        }
