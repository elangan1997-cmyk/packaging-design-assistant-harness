from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from packaging_assistant.models import PackagingJob, json_ready


class JobWorkspace:
    def __init__(self, root: str | Path, job: PackagingJob):
        self.root = Path(root).expanduser().resolve()
        self.job = job
        self.path = self.root / job.job_id

    def create(self) -> "JobWorkspace":
        self.path.mkdir(parents=True, exist_ok=False)
        self.write_json("request.json", {"action": self.job.workflow, "request_id": self.job.request_id})
        self.write_manifest()
        return self

    def write_json(self, name: str, payload: Any) -> Path:
        target = self.path / name
        target.write_text(
            json.dumps(json_ready(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return target

    def write_manifest(self) -> Path:
        return self.write_json("job.json", asdict(self.job))

