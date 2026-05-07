import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GUIDE = ROOT / "docs" / "PMBOT_SOURCE_004B_MANUAL_CAPTURE_OPERATOR_FILL_GUIDE.md"
CHECKLIST = (
    ROOT
    / "pm_bot"
    / "llm"
    / "manual_resolution_source_capture_operator_checklist.v1.json"
)
CHECKLIST_MD = (
    ROOT
    / "pm_bot"
    / "llm"
    / "manual_resolution_source_capture_operator_checklist.v1.md"
)


class ManualResolutionSourceCaptureOperatorChecklistTests(unittest.TestCase):
    def test_operator_fill_guide_and_checklist_exist(self):
        self.assertTrue(GUIDE.exists())
        self.assertTrue(CHECKLIST.exists())
        self.assertTrue(CHECKLIST_MD.exists())

    def test_checklist_json_parses_and_covers_all_markets(self):
        checklist = json.loads(CHECKLIST.read_text(encoding="utf-8"))

        self.assertEqual(
            checklist["checklist_version"],
            "manual_resolution_source_capture_operator_checklist.v1",
        )
        self.assertEqual(checklist["total_templates"], 14)
        self.assertEqual(len(checklist["per_market_checklist"]), 14)
        self.assertEqual(
            [item["market_id"] for item in checklist["per_market_checklist"]],
            [
                "563650",
                "569332",
                "569333",
                "569334",
                "569343",
                "569344",
                "569366",
                "569368",
                "569373",
                "573656",
                "597964",
                "598936",
                "691547",
                "692258",
            ],
        )

    def test_checklist_includes_fill_order_safety_and_no_authority_flags(self):
        checklist = json.loads(CHECKLIST.read_text(encoding="utf-8"))

        self.assertEqual(
            checklist["recommended_fill_order"][:4],
            [
                "full_market_resolution_criteria_text",
                "full_resolution_rules",
                "official_source_references",
                "official_source_urls_or_rule_references",
            ],
        )
        self.assertIn("no predictions", checklist["safety_do_not_include"])
        self.assertIn("no trading recommendations", checklist["safety_do_not_include"])
        self.assertIn("no probability", checklist["safety_do_not_include"])
        self.assertIn("no EV", checklist["safety_do_not_include"])
        self.assertIn("no edge", checklist["safety_do_not_include"])
        self.assertIn("no confidence score", checklist["safety_do_not_include"])
        self.assertIn("no side selection", checklist["safety_do_not_include"])
        self.assertIn("no buy/sell/hold/enter/exit", checklist["safety_do_not_include"])

        flags = checklist["no_authority_flags"]
        self.assertTrue(flags["operator_review_only"])
        self.assertTrue(flags["passive_context_only"])
        self.assertTrue(flags["no_trading_authority"])
        self.assertTrue(flags["no_queue_authority"])
        self.assertTrue(flags["no_runtime_authority"])
        self.assertTrue(flags["no_dispatcher_authority"])
        self.assertTrue(flags["no_wallet_or_order_authority"])
        self.assertTrue(flags["acceptance_is_not_trading_approval"])
        self.assertTrue(flags["no_market_action_guidance"])

    def test_per_market_entries_have_local_review_next_steps_only(self):
        checklist = json.loads(CHECKLIST.read_text(encoding="utf-8"))

        for item in checklist["per_market_checklist"]:
            self.assertEqual(item["current_status"], "not_started")
            self.assertEqual(item["validation_status"], "valid")
            self.assertTrue(item["no_market_action_guidance"])
            self.assertFalse(Path(item["capture_json_path"]).is_absolute())
            self.assertFalse(Path(item["capture_markdown_path"]).is_absolute())
            self.assertIn("manual local review", item["operator_next_step"])


if __name__ == "__main__":
    unittest.main()
