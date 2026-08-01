from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LegacyDielineAdapter:
    """Describes, but does not silently invoke, an external legacy generator.

    Phase 2 replaces this boundary with repository-owned deterministic models.
    A caller may supply an explicit executable path; user-specific paths are never embedded.
    """

    executable: Path | None = None

    @property
    def available(self) -> bool:
        return bool(self.executable and self.executable.is_file())

    def capability(self) -> dict[str, object]:
        return {
            "name": "legacy_dieline_adapter",
            "available": self.available,
            "execution_enabled": False,
            "reason": "Legacy geometry is not trusted until model-specific comparison tests pass.",
        }
