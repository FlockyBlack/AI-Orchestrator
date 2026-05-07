import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CAPTURE_DIR = ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture"
INVENTORY = ROOT / "pm_bot" / "llm" / "current_llm_market_packet_inventory.v1.json"


class ManualResolutionSourceCaptureTemplateTests(unittest.TestCase):
    def test_capture_directory_has_one_json_and_markdown_template_per_inventory_market(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        expected_market_ids = [item["market_id"] for item in inventory["markets"]]

        json_paths = sorted(CAPTURE_DIR.glob("*_resolution_source_capture.v1.json"))
        markdown_paths = sorted(CAPTURE_DIR.glob("*_resolution_source_capture.v1.md"))

        self.assertTrue(CAPTURE_DIR.exists())
        self.assertEqual(len(json_paths), 14)
        self.assertEqual(len(markdown_paths), 14)
        self.assertEqual(
            [path.name.split("_")[0] for path in json_paths],
            expected_market_ids,
        )
        self.assertEqual(
            [path.name.split("_")[0] for path in markdown_paths],
            expected_market_ids,
        )

    def test_capture_json_templates_have_status_and_no_authority_flags(self):
        for path in sorted(CAPTURE_DIR.glob("*_resolution_source_capture.v1.json")):
            packet = json.loads(path.read_text(encoding="utf-8"))

            self.assertEqual(packet["contract_version"], "manual_resolution_source_capture.v1")
            self.assertEqual(packet["source_capture_status"], "not_started")
            self.assertEqual(packet["capture_status"], "not_started")
            self.assertTrue(packet["no_market_action_guidance"])
            self.assertTrue(packet["operator_review_only"])
            self.assertTrue(packet["no_trading_authority"])
            self.assertTrue(packet["no_queue_authority"])
            self.assertTrue(packet["no_runtime_authority"])
            self.assertTrue(packet["no_wallet_or_order_authority"])
            self.assertIn("source_003_audit_reference", packet)
            self.assertIn("packet_inventory_reference", packet)
            self.assertIn("readiness_gate_reference", packet)

    def test_templates_leave_actual_resolution_source_fields_empty(self):
        for path in sorted(CAPTURE_DIR.glob("*_resolution_source_capture.v1.json")):
            packet = json.loads(path.read_text(encoding="utf-8"))

            self.assertEqual(packet["full_market_resolution_criteria_text"], "")
            self.assertEqual(packet["full_resolution_rules"], "")
            self.assertEqual(packet["official_source_references"], [])
            self.assertEqual(packet["official_source_urls_or_rule_references"], [])
            self.assertEqual(packet["source_timestamps"], [])
            self.assertEqual(packet["source_reliability_review"], "")
            self.assertEqual(packet["reviewed_local_evidence_references"], [])
            self.assertEqual(packet["non_placeholder_evidence_notes"], "")


if __name__ == "__main__":
    unittest.main()
