from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from packaging_assistant.api import generate_content_layout, run_packaging_request
from packaging_assistant.modules.structure import generate_structure_template


def _assets(root: Path) -> tuple[Path, Path, Path]:
    blank = root / "blank.svg"
    blank.write_text(
        generate_structure_template(
            {
                "model_code": "锁底盒",
                "dimensions": {"length": 80, "width": 40, "height": 120, "unit": "mm"},
            }
        ).svg,
        encoding="utf-8",
    )
    completed = root / "completed.svg"
    completed.write_text(
        generate_content_layout(
            {
                "template": str(blank),
                "brief": {
                    "brand": {"name": "测试品牌"},
                    "product": {"name": "测试产品", "net_content": "100 g"},
                },
            }
        ).svg,
        encoding="utf-8",
    )
    unclear = root / "unknown.txt"
    unclear.write_text("packaging asset with no machine-readable role", encoding="utf-8")
    return blank, completed, unclear


def _route(parameters: dict[str, object]) -> dict[str, object]:
    result = run_packaging_request({"action": "route", "parameters": parameters})
    if not result.success:
        raise AssertionError(result.error)
    return result.outputs[0]["inline"]


class RoutingMatrixTests(unittest.TestCase):
    def test_only_box_model_and_dimensions_routes_structure(self) -> None:
        decision = _route(
            {
                "model_code": "锁底盒",
                "dimensions": {"length": 80, "width": 40, "height": 120},
            }
        )
        self.assertEqual(decision["route"], "structure_template")

    def test_blank_dieline_and_product_data_routes_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            blank, _, _ = _assets(Path(tmp))
            decision = _route({"template": str(blank), "product_data": {"name": "测试产品"}})
        self.assertEqual(decision["route"], "content_layout")

    def test_completed_artwork_and_cmf_goal_routes_mockup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, completed, _ = _assets(Path(tmp))
            decision = _route(
                {
                    "artwork": str(completed),
                    "user_goal": "做 CMF 工艺效果图",
                    "dimensions": {"length": 80, "width": 40, "height": 120},
                }
            )
        self.assertEqual(decision["route"], "mockup_render")

    def test_dimensions_to_mockup_routes_multi_stage(self) -> None:
        decision = _route(
            {
                "model_code": "锁底盒",
                "dimensions": {"length": 80, "width": 40, "height": 120},
                "from_dimensions_to_mockup": True,
            }
        )
        self.assertEqual(decision["route"], "multi_stage_workflow")
        self.assertEqual(decision["next_action"], "structure_template")

    def test_unclear_file_routes_clarification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, _, unclear = _assets(Path(tmp))
            decision = _route({"input": str(unclear)})
        self.assertEqual(decision["route"], "clarification_required")
        self.assertTrue(decision["needs_clarification"])
        self.assertEqual(len(decision["evidence"]), 1)

    def test_mockup_goal_with_blank_dieline_routes_clarification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            blank, _, _ = _assets(Path(tmp))
            decision = _route({"artwork": str(blank), "user_goal": "生成包装效果图"})
        self.assertEqual(decision["route"], "clarification_required")
        self.assertIn("completed_artwork", decision["missing_fields"])

    def test_completed_artwork_and_dimensions_prefer_mockup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, completed, _ = _assets(Path(tmp))
            decision = _route(
                {
                    "artwork": str(completed),
                    "dimensions": {"length": 80, "width": 40, "height": 120},
                }
            )
        self.assertEqual(decision["route"], "mockup_render")

    def test_structure_template_with_information_routes_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            blank, _, _ = _assets(Path(tmp))
            decision = _route(
                {"template": str(blank), "brief": "${user_product_brief}", "user_goal": "加入包装信息"}
            )
        self.assertEqual(decision["route"], "content_layout")
        self.assertTrue(any(item.startswith("asset:") for item in decision["evidence"]))


if __name__ == "__main__":
    unittest.main()
