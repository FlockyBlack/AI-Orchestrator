import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROGRESS = ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_progress.v1.json"
PROGRESS_MD = ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_progress.v1.md"


class ManualResolutionSourceCaptureProgressTests(unittest.TestCase):
    def test_progress_json_and_markdown_exist(self):
        self.assertTrue(PROGRESS.exists())
        self.assertTrue(PROGRESS_MD.exists())

    def test_progress_reports_current_not_started_state(self):
        progress = json.loads(PROGRESS.read_text(encoding="utf-8"))

        self.assertEqual(progress["schema_version"], "manual_resolution_source_capture_progress.v1")
        self.assertEqual(progress["total_templates"], 14)
        self.assertEqual(progress["not_started_count"], 14)
        self.assertEqual(progress["draft_count"], 0)
        self.assertEqual(progress["ready_for_local_review_count"], 0)
        self.assertEqual(progress["reviewed_count"], 0)
        self.assertEqual(progress["needs_revision_count"], 0)
        self.assertEqual(progress["valid_template_count"], 14)
        self.assertEqual(progress["invalid_template_count"], 0)
        self.assertEqual(progress["markets_ready_for_local_review"], [])
        self.assertEqual(len(progress["markets_needing_operator_input"]), 14)

    def test_progress_reports_field_fill_counts(self):
        progress = json.loads(PROGRESS.read_text(encoding="utf-8"))

        for field in progress["next_fields_to_fill"]:
            self.assertEqual(progress["fields_filled_counts"][field], 0)
            self.assertEqual(progress["fields_missing_counts"][field], 14)

        self.assertEqual(
            progress["next_fields_to_fill"][:4],
            [
                "full_market_resolution_criteria_text",
                "full_resolution_rules",
                "official_source_references",
                "official_source_urls_or_rule_references",
            ],
        )

    def test_progress_safety_summary_is_no_authority(self):
        progress = json.loads(PROGRESS.read_text(encoding="utf-8"))
        safety = progress["safety_summary"]

        self.assertTrue(safety["operator_review_only"])
        self.assertTrue(safety["passive_context_only"])
        self.assertTrue(safety["no_trading_authority"])
        self.assertTrue(safety["no_queue_authority"])
        self.assertTrue(safety["no_runtime_authority"])
        self.assertTrue(safety["no_dispatcher_authority"])
        self.assertTrue(safety["no_wallet_or_order_authority"])
        self.assertTrue(safety["acceptance_is_not_trading_approval"])
        self.assertEqual(safety["openrouter_calls_performed"], 0)
        self.assertEqual(safety["polymarket_api_calls_performed"], 0)
        self.assertEqual(safety["external_network_calls_performed"], 0)


if __name__ == "__main__":
    unittest.main()
