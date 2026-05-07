import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INVENTORY_JSON = ROOT / "pm_bot" / "llm" / "current_llm_market_packet_inventory.v1.json"
AUDIT_JSON = ROOT / "pm_bot" / "llm" / "current_llm_source_evidence_completeness_audit.v1.json"
AUDIT_MD = ROOT / "pm_bot" / "llm" / "current_llm_source_evidence_completeness_audit.v1.md"


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class CurrentLlmSourceEvidenceCompletenessAuditTests(unittest.TestCase):
    def test_evidence_audit_exists_and_matches_reviewed_inventory(self):
        inventory = _load_json(INVENTORY_JSON)
        audit = _load_json(AUDIT_JSON)
        reviewed_inventory_ids = {
            item["market_id"] for item in inventory["markets"] if item["already_reviewed_by_openrouter"]
        }
        reviewed_audit_ids = {item["market_id"] for item in audit["reviewed_markets"]}

        self.assertTrue(AUDIT_MD.exists())
        self.assertEqual(audit["schema_version"], "current_llm_source_evidence_completeness_audit.v1")
        self.assertEqual(audit["status"], "source_evidence_completeness_audit_created")
        self.assertEqual(reviewed_audit_ids, reviewed_inventory_ids)
        self.assertEqual(audit["aggregate"]["reviewed_market_count"], 10)

    def test_each_reviewed_market_has_expected_audit_fields(self):
        audit = _load_json(AUDIT_JSON)

        for item in audit["reviewed_markets"]:
            self.assertIn(item["category"], {"legal/courts", "elections", "crypto"})
            self.assertIs(item["has_resolution_source_or_rules"], False)
            self.assertIs(item["has_local_context"], True)
            self.assertIs(item["has_source_gap_notes"], True)
            self.assertIs(item["has_missing_evidence_notes"], True)
            self.assertIs(item["has_contradiction_checks"], True)
            self.assertIs(item["has_risk_notes"], True)
            self.assertIs(item["has_operator_checklist"], True)
            self.assertEqual(item["evidence_completeness_level"], "medium")
            self.assertIs(item["needs_manual_source_review"], True)
            self.assertIs(item["needs_local_enrichment_before_future_llm_review"], True)
            self.assertIn("Manual source review", item["sanitized_notes"])

    def test_evidence_audit_aggregate_is_deterministic(self):
        audit = _load_json(AUDIT_JSON)
        aggregate = audit["aggregate"]

        self.assertEqual(aggregate["evidence_completeness_counts"], {"medium": 10})
        self.assertIn("full_market_resolution_criteria_text", aggregate["common_missing_fields"])
        self.assertIn("official_source_urls", aggregate["common_missing_fields"])
        self.assertIn("elections", aggregate["category_specific_gaps"])
        self.assertIn("crypto", aggregate["category_specific_gaps"])
        self.assertIn("legal/courts", aggregate["category_specific_gaps"])
        self.assertIn("official_election_authority_identifier", aggregate["category_specific_gaps"]["elections"])
        self.assertIn("benchmark_and_timezone_rules", aggregate["category_specific_gaps"]["crypto"])
        self.assertIn("docket_identifier", aggregate["category_specific_gaps"]["legal/courts"])
        self.assertEqual(
            aggregate["top_local_enrichment_priorities"],
            [
                "resolution source extraction",
                "category labeling",
                "source gap normalization",
                "operator checklist standardization",
                "local packet completeness score",
            ],
        )

    def test_evidence_audit_safety_counters_are_zero(self):
        audit = _load_json(AUDIT_JSON)

        self.assertEqual(audit["network_calls_performed"], 0)
        self.assertEqual(audit["polymarket_api_calls_performed"], 0)
        self.assertEqual(audit["openrouter_calls_performed"], 0)
        self.assertFalse(audit["safety_summary"]["api_key_accessed"])


if __name__ == "__main__":
    unittest.main()
