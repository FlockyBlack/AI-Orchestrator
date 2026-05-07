import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / "pm_bot" / "llm" / "current_llm_resolution_source_normalization_audit.v1.json"
EXPECTED_MARKET_IDS = {
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
}


class CurrentResolutionSourceNormalizationAuditTests(unittest.TestCase):
    def test_audit_exists_parses_and_covers_inventory(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))

        self.assertEqual(
            audit["schema_version"],
            "current_llm_resolution_source_normalization_audit.v1",
        )
        self.assertEqual(audit["status"], "resolution_source_normalization_audit_created")
        self.assertEqual({item["market_id"] for item in audit["markets"]}, EXPECTED_MARKET_IDS)
        self.assertEqual({item["market_id"] for item in audit["per_market_audit"]}, EXPECTED_MARKET_IDS)
        self.assertEqual(audit["aggregate"]["total_markets_audited"], 14)
        self.assertEqual(audit["total_markets_audited"], 14)

    def test_missing_source_fields_are_explicit_and_not_fabricated(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))

        for record in audit["markets"]:
            missing = record["missing_resolution_source_fields"]
            self.assertIn("full_market_resolution_criteria_text", missing)
            self.assertIn("full_resolution_rules", missing)
            self.assertIn("official_source_references", missing)
            self.assertIn("official_source_urls_or_rule_references", missing)
            self.assertFalse(record["resolution_criteria_text_present"])
            self.assertIsNone(record["full_market_resolution_criteria_text"])
            self.assertFalse(record["full_resolution_rules_present"])
            self.assertIsNone(record["full_resolution_rules"])
            self.assertFalse(record["official_source_references_present"])
            self.assertEqual(record["official_source_references"], [])
            self.assertFalse(record["official_source_urls_or_rule_references_present"])
            self.assertEqual(record["official_source_urls_or_rule_references"], [])
            self.assertTrue(record["needs_manual_resolution_source_review"])
            self.assertTrue(record["no_market_action_guidance"])

        aggregate = audit["aggregate"]
        self.assertEqual(aggregate["markets_missing_resolution_criteria_text"], 14)
        self.assertEqual(aggregate["markets_missing_full_resolution_rules"], 14)
        self.assertEqual(aggregate["markets_missing_official_source_references"], 14)
        self.assertEqual(
            aggregate["markets_missing_official_source_urls_or_rule_references"],
            14,
        )


if __name__ == "__main__":
    unittest.main()
