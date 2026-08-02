from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from packaging_assistant.api import inspect_packaging_asset, run_packaging_request
from packaging_assistant.capabilities import capability_report
from packaging_assistant.modules.mockup import LegacyCMFAdapter
from packaging_assistant.modules.structure import (
    LegacyDielineAdapter,
    generate_structure_template,
    model_report,
)
from packaging_assistant.providers import MockProvider, ProviderRequest


SVG_NS = "{http://www.w3.org/2000/svg}"
PT_PER_MM = 72 / 25.4


def _tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _numbers(value: str) -> list[float]:
    return [float(item) for item in re.findall(r"[-+]?(?:\d*\.\d+|\d+)", value)]


def _original_group_primitives(path: Path, group_index: int) -> tuple[list[tuple], list[tuple]]:
    root = ET.parse(path).getroot()
    group = root.findall(f"{SVG_NS}g")[group_index]
    crease_group, cut_group = list(group)[:2]

    def parse(container: ET.Element) -> list[tuple]:
        result: list[tuple] = []
        for item in list(container):
            kind = _tag(item)
            if kind == "path" and not item.attrib.get("d", "").strip():
                continue
            if kind == "line":
                values = [float(item.attrib[key]) / PT_PER_MM for key in ("x1", "y1", "x2", "y2")]
                result.append((kind, (), values))
            elif kind == "polyline":
                result.append((kind, (), [value / PT_PER_MM for value in _numbers(item.attrib["points"])]))
            elif kind == "path":
                d = item.attrib["d"]
                commands = tuple(re.findall(r"[A-Za-z]", d))
                result.append((kind, commands, [value / PT_PER_MM for value in _numbers(d)]))
        return result

    return parse(crease_group), parse(cut_group)


def _translated_path_values(commands: tuple[str, ...], values: list[float], dx: float, dy: float) -> list[float]:
    sizes = {"M": 2, "L": 2, "C": 6, "H": 1, "c": 6, "h": 1, "l": 2, "v": 1, "z": 0}
    translated: list[float] = []
    index = 0
    for command in commands:
        size = sizes[command]
        current = values[index:index + size]
        if command in {"M", "L", "C"}:
            for pair_index in range(0, size, 2):
                current[pair_index] += dx
                current[pair_index + 1] += dy
        elif command == "H":
            current[0] += dx
        translated.extend(current)
        index += size
    return translated


def _original_carry_primitives(path: Path, baseline_y: float) -> tuple[list[tuple], list[tuple]]:
    root = ET.parse(path).getroot()
    group = root.findall(f"{SVG_NS}g")[1]

    def parse(items: list[ET.Element]) -> list[tuple]:
        result: list[tuple] = []
        for item in items:
            kind = _tag(item)
            if kind == "path" and not item.attrib.get("d", "").strip():
                continue
            if kind == "line":
                values = [float(item.attrib[key]) / PT_PER_MM for key in ("x1", "y1", "x2", "y2")]
                values[1] -= baseline_y
                values[3] -= baseline_y
                result.append((kind, (), values))
            elif kind == "polyline":
                values = [value / PT_PER_MM for value in _numbers(item.attrib["points"])]
                for index in range(1, len(values), 2):
                    values[index] -= baseline_y
                result.append((kind, (), values))
            elif kind == "path":
                commands = tuple(re.findall(r"[A-Za-z]", item.attrib["d"]))
                values = [value / PT_PER_MM for value in _numbers(item.attrib["d"])]
                result.append((kind, commands, _translated_path_values(commands, values, 0, -baseline_y)))
        return result

    children = list(group)
    return parse(list(children[0])), parse(list(children[1]) + children[2:])


def _generated_primitives(svg: str, layer_id: str) -> list[tuple]:
    root = ET.fromstring(svg)
    layer = next(item for item in root.findall(f"{SVG_NS}g") if item.attrib.get("id") == layer_id)
    result: list[tuple] = []
    for item in list(layer):
        kind = _tag(item)
        if kind == "line":
            values = [float(item.attrib[key]) for key in ("x1", "y1", "x2", "y2")]
            result.append((kind, (), values))
        elif kind == "polyline":
            result.append((kind, (), _numbers(item.attrib["points"])))
        elif kind == "path":
            result.append((kind, tuple(item.attrib["data-commands"].split()), _numbers(item.attrib["d"])))
    return result


def _assert_primitives_equal(test: unittest.TestCase, actual: list[tuple], expected: list[tuple]) -> None:
    test.assertEqual(len(actual), len(expected))
    for index, (actual_item, expected_item) in enumerate(zip(actual, expected)):
        test.assertEqual(actual_item[0], expected_item[0], f"primitive {index} kind")
        test.assertEqual(actual_item[1], expected_item[1], f"primitive {index} commands")
        test.assertEqual(len(actual_item[2]), len(expected_item[2]), f"primitive {index} value count")
        for number_index, (left, right) in enumerate(zip(actual_item[2], expected_item[2])):
            test.assertAlmostEqual(left, right, places=3, msg=f"primitive {index} value {number_index}")


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

    def test_unfinished_structure_model_is_honestly_not_implemented(self) -> None:
        result = run_packaging_request(
            {
                "action": "structure_template",
                "parameters": {
                    "model_code": "直线盒",
                    "dimensions": {"length": 80, "width": 40, "height": 120, "unit": "mm"},
                },
            }
        )
        self.assertFalse(result.success)
        self.assertEqual(result.status, "not_implemented")
        self.assertEqual(result.error["code"], "NOT_IMPLEMENTED")

    def test_box_v2_models_are_independently_registered(self) -> None:
        models = model_report()
        self.assertEqual(len(models), 10)
        self.assertEqual(len({item["code"] for item in models}), 10)
        implemented = [item["name_zh"] for item in models if item["implemented"]]
        self.assertEqual(implemented, ["锁底盒", "手提盒"])

    def test_lock_bottom_structure_job_writes_three_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_packaging_request(
                {
                    "action": "structure_template",
                    "request_id": "lock-bottom",
                    "parameters": {
                        "model_code": "锁底盒",
                        "dimensions": {
                            "length": 80,
                            "width": 40,
                            "height": 120,
                            "unit": "mm",
                            "dimension_type": "finished_outer",
                        },
                    },
                },
                tmp,
            )
            self.assertTrue(result.success)
            self.assertEqual({Path(item["path"]).name for item in result.outputs}, {"template.svg", "structure_spec.json", "validation_report.json"})
            self.assertTrue((Path(tmp) / result.job_id / "job.json").is_file())

    def test_lock_bottom_svg_is_deterministic_and_layered(self) -> None:
        parameters = {
            "model_code": "carton.box_v2.lock_bottom",
            "dimensions": {"length": 100, "width": 55, "height": 160, "unit": "mm"},
            "shrink": 0.7,
            "tuck_height": 15,
            "glue_width": 14,
        }
        first = generate_structure_template(parameters)
        second = generate_structure_template(parameters)
        self.assertEqual(first.svg, second.svg)
        root = ET.fromstring(first.svg)
        layer_ids = {item.attrib.get("id") for item in root.findall(f"{SVG_NS}g")}
        self.assertTrue({"LAYER_CUT", "LAYER_CREASE", "LAYER_BLEED", "LAYER_SAFE", "LAYER_CONTENT_GUIDES"}.issubset(layer_ids))
        self.assertIn("REQUIRES_MANUFACTURER_REVIEW", first.svg)
        self.assertEqual(first.validation["counts"]["cut_primitives"], 16)
        self.assertEqual(first.validation["counts"]["crease_primitives"], 7)

    def test_lock_bottom_matches_original_script_at_80x40x120(self) -> None:
        generated = generate_structure_template(
            {
                "model_code": "锁底盒",
                "dimensions": {"length": 80, "width": 40, "height": 120, "unit": "mm"},
                "shrink": 0.5,
                "tuck_height": 12,
                "glue_width": 11,
            }
        )
        original_crease, original_cut = _original_group_primitives(
            ROOT / "tests/fixtures/original-script/box-v2-lock-bottom-80x40x120.svg", 2
        )
        _assert_primitives_equal(self, _generated_primitives(generated.svg, "LAYER_CREASE"), original_crease)
        _assert_primitives_equal(self, _generated_primitives(generated.svg, "LAYER_CUT"), original_cut)

    def test_carry_handle_matches_original_script_at_100x60x160(self) -> None:
        generated = generate_structure_template(
            {
                "model_code": "手提盒",
                "dimensions": {"length": 100, "width": 60, "height": 160, "unit": "mm"},
                "shrink": 0.5,
                "tuck_height": 12,
                "glue_width": 11,
            }
        )
        original_crease, original_cut = _original_carry_primitives(
            ROOT / "tests/fixtures/original-script/box-v2-carry-handle-100x60x160.svg", 297.0
        )
        _assert_primitives_equal(self, _generated_primitives(generated.svg, "LAYER_CREASE"), original_crease)
        _assert_primitives_equal(self, _generated_primitives(generated.svg, "LAYER_CUT"), original_cut)

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
        self.assertTrue(report["actions"]["structure_template"]["implemented"])
        self.assertEqual(len(report["structure_models"]), 10)
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
