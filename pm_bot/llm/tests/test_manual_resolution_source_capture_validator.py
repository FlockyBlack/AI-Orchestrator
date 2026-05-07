import importlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_validation.v1.json"


class ManualResolutionSourceCaptureValidatorTests(unittest.TestCase):
    def test_validator_module_imports(self):
        module = importlib.import_module("pm_bot.llm.manual_resolution_source_capture_validator")
        self.assertTrue(hasattr(module, "build_validation_report"))

    def test_validation_report_exists_and_reports_all_templates_valid(self):
        report = json.loads(VALIDATION.read_text(encoding="utf-8"))

        self.assertEqual(report["schema_version"], "manual_resolution_source_capture_validation.v1")
        self.assertEqual(report["capture_schema_version"], "manual_resolution_source_capture_schema.v1")
        self.assertEqual(report["total_packets_validated"], 14)
        self.assertEqual(report["valid_count"], 14)
        self.assertEqual(report["invalid_count"], 0)
        self.assertEqual(report["packets_missing_required_template_fields"], [])
        self.assertEqual(report["packets_with_market_action_guidance"], [])
        self.assertEqual(len(report["packets_ready_for_local_review"]), 0)
        self.assertEqual(len(report["packets_not_started"]), 14)

    def test_validator_rejects_ready_packets_with_empty_high_completeness_fields(self):
        module = importlib.import_module("pm_bot.llm.manual_resolution_source_capture_validator")
        schema = json.loads(
            (ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_schema.v1.json").read_text(
                encoding="utf-8"
            )
        )
        packet_path = next(
            (ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture").glob(
                "*_resolution_source_capture.v1.json"
            )
        )
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        packet["capture_status"] = "ready_for_local_review"
        packet["source_capture_status"] = "ready_for_local_review"

        result = module.validate_capture_packet(packet, schema)

        self.assertFalse(result["valid"])
        self.assertIn("empty_high_completeness_fields_for_review_status", result["errors"])


if __name__ == "__main__":
    unittest.main()
