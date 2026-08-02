from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from packaging_assistant.api import generate_content_layout, generate_mockup, run_packaging_request
from packaging_assistant.modules.structure import generate_structure_template
from packaging_assistant.providers import (
    MockProvider,
    ModelCapabilities,
    OpenAICompatibleProvider,
    ProviderConfig,
    ProviderExecutor,
    ProviderRequest,
    ProviderResponse,
)
from packaging_assistant.providers.mock import MOCK_PNG_BASE64


def _completed_artwork(directory: Path) -> Path:
    template = directory / "template.svg"
    template.write_text(
        generate_structure_template(
            {
                "model_code": "锁底盒",
                "dimensions": {"length": 80, "width": 40, "height": 120, "unit": "mm"},
            }
        ).svg,
        encoding="utf-8",
    )
    generation = generate_content_layout(
        {
            "template": str(template),
            "brief": {
                "jurisdiction": "CN",
                "brand": {"name": "测试品牌"},
                "product": {"name": "观赏鱼专用盐", "net_content": "500 g"},
            },
        }
    )
    artwork = directory / "completed-artwork.svg"
    artwork.write_text(generation.svg, encoding="utf-8")
    return artwork


def _parameters(artwork: Path, provider: MockProvider | None = None) -> dict[str, object]:
    return {
        "artwork": str(artwork),
        "dimensions": {"length": 80, "width": 40, "height": 120, "unit": "mm"},
        "structure": "lock-bottom folding carton",
        "material": "350 gsm SBS paperboard",
        "finishes": [{"type": "foil", "target": "brand mark"}],
        "allow_mock": True,
        "_providers": [provider or MockProvider()],
    }


class NamedMock(MockProvider):
    def __init__(self, name: str, scripted: list[ProviderResponse]) -> None:
        super().__init__(scripted)
        self.name = name


class ModuleCContractTests(unittest.TestCase):
    def test_missing_dimensions_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artwork = _completed_artwork(Path(tmp))
            result = run_packaging_request(
                {"action": "mockup_render", "parameters": {"artwork": str(artwork), "material": "paper"}}
            )
            self.assertFalse(result.success)
            self.assertEqual(result.status, "needs_input")
            self.assertIn("dimensions", result.route["missing_fields"])

    def test_blank_dieline_requires_completed_artwork(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            blank = Path(tmp) / "blank.svg"
            blank.write_text(
                generate_structure_template(
                    {
                        "model_code": "锁底盒",
                        "dimensions": {"length": 80, "width": 40, "height": 120, "unit": "mm"},
                    }
                ).svg,
                encoding="utf-8",
            )
            result = run_packaging_request(
                {
                    "action": "mockup_render",
                    "parameters": {
                        "artwork": str(blank),
                        "dimensions": {"length": 80, "width": 40, "height": 120},
                        "material": "paperboard",
                    },
                }
            )
            self.assertFalse(result.success)
            self.assertEqual(result.status, "needs_input")
            self.assertIn("completed_artwork", result.route["missing_fields"])

    def test_mock_provider_flow_is_explicit_and_writes_six_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artwork = _completed_artwork(root)
            provider = MockProvider()
            result = run_packaging_request(
                {"action": "mockup_render", "request_id": "mock-cmf", "parameters": _parameters(artwork, provider)},
                root / "jobs",
            )
            self.assertTrue(result.success)
            self.assertEqual(result.status, "manual_review")
            self.assertIn("MOCK_OUTPUT_NOT_A_REAL_CMF_RENDER", result.warnings)
            self.assertEqual(len(provider.calls), 3)
            output_names = {Path(item["path"]).name for item in result.outputs}
            self.assertEqual(
                output_names,
                {
                    "mockup.png",
                    "cmf-plan.json",
                    "generation-record.json",
                    "visual-qa.json",
                    "retry-record.json",
                    "review-checklist.md",
                },
            )
            job_root = root / "jobs" / result.job_id
            record = json.loads((job_root / "generation-record.json").read_text(encoding="utf-8"))
            plan = json.loads((job_root / "cmf-plan.json").read_text(encoding="utf-8"))
            self.assertTrue(record["mock"])
            self.assertFalse(record["production_file"])
            self.assertTrue(any("logo" in rule.lower() for rule in plan["protection_rules"]))
            self.assertTrue(any("dielines" in rule.lower() for rule in plan["protection_rules"]))

    def test_mockup_cli_executes_provider_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artwork = _completed_artwork(root)
            config = root / "mock.json"
            config.write_text(
                json.dumps(
                    {
                        "mockup": {
                            "dimensions": {"length": 80, "width": 40, "height": 120},
                            "material": "paperboard",
                            "allow_mock": True,
                        },
                        "providers": [{"name": "mock", "type": "mock", "enabled": True}],
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "packaging_assistant.cli",
                    "--output",
                    str(root / "jobs"),
                    "mockup",
                    "--artwork",
                    str(artwork),
                    "--config",
                    str(config),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 0)
            self.assertTrue(payload["success"])
            self.assertEqual(payload["status"], "manual_review")
            self.assertEqual(len(payload["outputs"]), 6)

    def test_mock_provider_output_is_reproducible(self) -> None:
        request = ProviderRequest("image_generation", {"material": "paper", "finish": "foil"})
        first = MockProvider().invoke(request)
        second = MockProvider().invoke(request)
        self.assertEqual(first.output, second.output)

    def test_visual_qa_retries_are_bounded(self) -> None:
        retry_qa = {
            "passed": False,
            "score": 0.5,
            "issues": [
                {
                    "type": "text_distortion",
                    "severity": "high",
                    "region": "front",
                    "message": "Chinese text changed",
                    "retryable": True,
                }
            ],
            "recommended_action": "retry",
        }
        responses = [ProviderResponse(True, "scripted", {"inspection": "ok"})]
        for _ in range(3):
            responses.extend(
                [
                    ProviderResponse(
                        True,
                        "scripted",
                        {"image_base64": MOCK_PNG_BASE64, "mime_type": "image/png"},
                    ),
                    ProviderResponse(True, "scripted", retry_qa),
                ]
            )
        provider = NamedMock("scripted", responses)
        with tempfile.TemporaryDirectory() as tmp:
            artwork = _completed_artwork(Path(tmp))
            generation = generate_mockup({**_parameters(artwork, provider), "max_qa_retries": 2})
        self.assertEqual(sum(call.operation == "image_generation" for call in provider.calls), 3)
        self.assertEqual(generation.retry_record["qa_retries_used"], 2)
        self.assertEqual(generation.status, "manual_review")

    def test_provider_retry_and_fallback_order(self) -> None:
        first = NamedMock(
            "first",
            [
                ProviderResponse(False, "first", error={"code": "TIMEOUT"}, retryable=True),
                ProviderResponse(False, "first", error={"code": "TIMEOUT"}, retryable=False),
            ],
        )
        second = NamedMock("second", [ProviderResponse(True, "second", {"ok": True})])
        execution = ProviderExecutor([first, second]).execute(
            "vision", ProviderRequest("visual_qa", {}), retries_per_provider=1
        )
        self.assertTrue(execution.response.success)
        self.assertEqual([item["provider"] for item in execution.attempts], ["first", "first", "second"])

    def test_search_provider_unavailable_is_explicit(self) -> None:
        provider = NamedMock("vision-only", [])
        provider.capabilities = ModelCapabilities(vision=True)
        result = ProviderExecutor([provider]).execute("search", ProviderRequest("search", {}))
        self.assertFalse(result.response.success)
        self.assertEqual(result.response.error["code"], "PROVIDER_UNAVAILABLE")

    def test_api_key_value_never_enters_provider_error(self) -> None:
        secret = "super-secret-test-value"
        os.environ["PACKAGING_TEST_SECRET"] = secret
        try:
            provider = OpenAICompatibleProvider(
                ProviderConfig(
                    name="configured",
                    provider_type="openai_compatible",
                    endpoint="",
                    api_key_env="PACKAGING_TEST_SECRET",
                    capabilities=ModelCapabilities(vision=True),
                )
            )
            response = provider.invoke(ProviderRequest("visual_qa", {}))
            self.assertNotIn(secret, json.dumps(response.error, ensure_ascii=False))
        finally:
            os.environ.pop("PACKAGING_TEST_SECRET", None)

    def test_rest_provider_timeout_is_retryable_and_sanitized(self) -> None:
        provider = OpenAICompatibleProvider(
            ProviderConfig(
                name="timeout-provider",
                provider_type="openai_compatible",
                endpoint="https://provider.invalid/generate",
                capabilities=ModelCapabilities(image_generation=True),
            )
        )
        with patch("urllib.request.urlopen", side_effect=TimeoutError("sensitive transport detail")):
            response = provider.invoke(ProviderRequest("image_generation", {}))
        self.assertFalse(response.success)
        self.assertTrue(response.retryable)
        self.assertEqual(response.error["code"], "PROVIDER_TIMEOUT")
        self.assertNotIn("sensitive transport detail", json.dumps(response.error, ensure_ascii=False))

    def test_flexible_and_bottle_rules_are_engineered_into_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artwork = _completed_artwork(Path(tmp))
            flexible = generate_mockup(
                {**_parameters(artwork), "structure": "flexible pouch with heat-seal edges"}
            )
            bottle = generate_mockup(
                {**_parameters(artwork), "structure": "PET bottle with wrap label"}
            )
        self.assertTrue(any("heat seals" in rule for rule in flexible.cmf_plan["protection_rules"]))
        self.assertTrue(any("bottle geometry" in rule for rule in bottle.cmf_plan["protection_rules"]))

    def test_mock_image_fixture_is_png(self) -> None:
        self.assertEqual(base64.b64decode(MOCK_PNG_BASE64)[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
