from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from packaging_assistant.api import inspect_packaging_asset, run_packaging_request
from packaging_assistant.capabilities import capability_report
from packaging_assistant.modules.mockup import LegacyCMFAdapter
from packaging_assistant.modules.structure import LegacyDielineAdapter
from packaging_assistant.providers import MockProvider, ProviderRequest


class HarnessContractTests(unittest.TestCase):
    def test_health_check(self) -> None:
        result = run_packaging_request({"action": "health_check", "parameters": {}})
        self.assertTrue(result.success)
        self.assertEqual(result.status, "completed")
        health = result.outputs[0]["inline"]
        self.assertFalse(health["web_required"])
        self.assertFalse(health["node_required"])

    def test_missing_action_is_machine_readable(self) -> None:
        result = run_packaging_request({"parameters": {}})
        self.assertFalse(result.success)
        self.assertEqual(result.error["code"], "MISSING_REQUIRED_FIELD")

    def test_unknown_action_is_rejected(self) -> None:
        result = run_packaging_request({"action": "magic", "parameters": {}})
        self.assertEqual(result.error["code"], "UNSUPPORTED_ACTION")

    def test_structure_dry_run_reports_missing_fields(self) -> None:
        result = run_packaging_request(
            {"action": "structure_template", "parameters": {}}, dry_run=True
        )
        self.assertTrue(result.success)
        self.assertEqual(result.status, "dry_run")
        self.assertEqual(result.route["missing_fields"], ["model_code", "dimensions"])

    def test_structure_is_honestly_not_implemented(self) -> None:
        result = run_packaging_request(
            {
                "action": "structure_template",
                "parameters": {
                    "model_code": "carton.reverse_tuck_end",
                    "dimensions": {"length": 80, "width": 40, "height": 120, "unit": "mm"},
                },
            }
        )
        self.assertFalse(result.success)
        self.assertEqual(result.status, "not_implemented")
        self.assertEqual(result.error["code"], "NOT_IMPLEMENTED")

    def test_mockup_dry_run_never_calls_provider(self) -> None:
        result = run_packaging_request(
            {"action": "mockup_render", "parameters": {"artwork": "design.ai"}},
            dry_run=True,
        )
        self.assertTrue(result.success)
        self.assertTrue(result.route["may_incur_cost"])
        self.assertEqual(result.route["providers"], ["image_generation", "vision"])

    def test_job_workspace_is_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = run_packaging_request(
                {"action": "health_check", "request_id": "one", "parameters": {}}, tmp
            )
            second = run_packaging_request(
                {"action": "health_check", "request_id": "two", "parameters": {}}, tmp
            )
            self.assertNotEqual(first.job_id, second.job_id)
            self.assertTrue((Path(tmp) / first.job_id / "job.json").is_file())
            self.assertTrue((Path(tmp) / second.job_id / "health_report.json").is_file())

    def test_svg_asset_inspection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            svg = Path(tmp) / "sample.svg"
            svg.write_text('<svg><metadata>model</metadata><g id="LAYER_CUT"/></svg>', encoding="utf-8")
            asset = inspect_packaging_asset(svg)
            self.assertEqual(asset.type, "svg")
            self.assertTrue(asset.metadata["has_dieline"])
            self.assertTrue(asset.metadata["has_structure_metadata"])

    def test_json_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "valid.json"
            path.write_text('{"ok": true}', encoding="utf-8")
            result = run_packaging_request(
                {"action": "validate", "parameters": {"file": str(path)}}
            )
            self.assertTrue(result.outputs[0]["inline"]["valid"])

    def test_invalid_json_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.json"
            path.write_text("{", encoding="utf-8")
            result = run_packaging_request(
                {"action": "validate", "parameters": {"file": str(path)}}
            )
            self.assertFalse(result.outputs[0]["inline"]["valid"])

    def test_capability_manifest_is_explicit(self) -> None:
        report = capability_report()
        self.assertTrue(report["actions"]["health_check"]["implemented"])
        self.assertFalse(report["actions"]["content_layout"]["implemented"])
        self.assertFalse(report["actions"]["mockup_render"]["implemented"])

    def test_mock_provider_has_no_external_effect(self) -> None:
        response = MockProvider().invoke(ProviderRequest("render", {"x": 1}))
        self.assertTrue(response.success)
        self.assertTrue(response.output["mock"])

    def test_legacy_dieline_adapter_does_not_guess_path(self) -> None:
        adapter = LegacyDielineAdapter()
        self.assertFalse(adapter.available)
        self.assertFalse(adapter.capability()["execution_enabled"])

    def test_legacy_cmf_references_are_preserved(self) -> None:
        adapter = LegacyCMFAdapter(ROOT)
        self.assertTrue(adapter.capability()["advisory_available"])
        self.assertFalse(adapter.capability()["rendering_available"])

    def test_skill_entry_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            output = Path(tmp) / "output"
            request.write_text(
                json.dumps({"action": "health_check", "request_id": "entry", "parameters": {}}),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "skill_entry.py"),
                    "--request",
                    str(request),
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 0)
            self.assertTrue(payload["success"])
            self.assertTrue((output / payload["job_id"] / "job.json").is_file())


if __name__ == "__main__":
    unittest.main()

