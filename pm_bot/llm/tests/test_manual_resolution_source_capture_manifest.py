import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_manifest.v1.json"


class ManualResolutionSourceCaptureManifestTests(unittest.TestCase):
    def test_manifest_exists_and_reports_expected_counts(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

        self.assertEqual(manifest["schema_version"], "manual_resolution_source_capture_manifest.v1")
        self.assertEqual(manifest["total_capture_packets"], 14)
        self.assertEqual(len(manifest["packet_paths"]), 14)
        self.assertEqual(len(manifest["markdown_paths"]), 14)
        self.assertEqual(manifest["capture_status_counts"]["not_started"], 14)
        self.assertEqual(manifest["capture_status_counts"]["ready_for_local_review"], 0)
        self.assertEqual(manifest["reviewed_vs_unreviewed"]["reviewed_accepted"], 10)
        self.assertEqual(manifest["reviewed_vs_unreviewed"]["not_reviewed"], 4)
        self.assertEqual(manifest["readiness_band_counts"]["medium"], 10)
        self.assertEqual(manifest["readiness_band_counts"]["low"], 4)

    def test_manifest_operator_fill_order_and_missing_fields_are_explicit(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        expected_order = [
            "full_market_resolution_criteria_text",
            "full_resolution_rules",
            "official_source_references",
            "official_source_urls_or_rule_references",
            "source_timestamps",
            "source_reliability_review",
            "reviewed_local_evidence_references",
            "non_placeholder_evidence_notes",
        ]

        self.assertEqual(manifest["recommended_operator_fill_order"], expected_order)
        missing_counts = {
            item["field"]: item["market_count"]
            for item in manifest["fields_missing_across_all_packets"]
        }
        for field in expected_order:
            self.assertEqual(missing_counts[field], 14)

    def test_manifest_safety_flags_are_no_authority(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

        self.assertTrue(manifest["no_market_action_guidance"])
        self.assertTrue(manifest["operator_review_only"])
        self.assertTrue(manifest["no_trading_authority"])
        self.assertTrue(manifest["no_queue_authority"])
        self.assertTrue(manifest["no_runtime_authority"])
        self.assertTrue(manifest["no_wallet_or_order_authority"])


if __name__ == "__main__":
    unittest.main()
