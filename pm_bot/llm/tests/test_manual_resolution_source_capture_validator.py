import importlib
import json
import subprocess
import sys
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
        self.assertEqual(len(report["packets_not_started"]), 13)
        self.assertNotIn("597964", report["packets_not_started"])
        self.assertIn("operator_next_steps", report)
        self.assertIn("missing_fields_by_priority", report)
        self.assertEqual(report["missing_fields_by_priority"][0]["field"], "full_market_resolution_criteria_text")
        self.assertEqual(report["missing_fields_by_priority"][0]["market_count"], 13)
        self.assertIn("Fill", report["packet_results"][0]["operator_next_step"])
        draft_result = next(
            item for item in report["packet_results"] if item["market_id"] == "597964"
        )
        self.assertEqual(draft_result["capture_status"], "draft")
        self.assertEqual(draft_result["missing_fields_by_priority"], [])

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

    def test_strict_ready_requires_all_priority_fields_for_ready_packets(self):
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
        packet["full_market_resolution_criteria_text"] = "local operator criteria text"
        packet["full_resolution_rules"] = "local operator rules text"
        packet["official_source_references"] = ["local official source label"]
        packet["official_source_urls_or_rule_references"] = ["local rule reference"]

        result = module.validate_capture_packet(packet, schema, strict_ready=True)

        self.assertFalse(result["valid"])
        self.assertIn("strict_ready_required_fields_empty", result["errors"])
        self.assertIn("source_timestamps", result["strict_ready_missing_fields"])

    def test_summary_only_and_market_id_cli_flags(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pm_bot.llm.manual_resolution_source_capture_validator",
                "--market-id",
                "563650",
                "--summary-only",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        summary = json.loads(result.stdout)

        self.assertEqual(summary["total_packets_validated"], 1)
        self.assertEqual(summary["valid_count"], 1)
        self.assertEqual(summary["invalid_count"], 0)
        self.assertIn("operator_next_steps", summary)


if __name__ == "__main__":
    unittest.main()
