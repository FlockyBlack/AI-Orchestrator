import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCHEMA = ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_schema.v1.json"


REQUIRED_FIELDS = {
    "market_id",
    "market_title_or_question",
    "category",
    "capture_status",
    "full_market_resolution_criteria_text",
    "full_resolution_rules",
    "official_source_references",
    "official_source_urls_or_rule_references",
    "source_timestamps",
    "source_reliability_review",
    "reviewed_local_evidence_references",
    "non_placeholder_evidence_notes",
    "jurisdiction",
    "candidate_or_party_if_applicable",
    "manual_operator_notes",
    "unresolved_source_questions",
    "source_capture_author_or_operator",
    "source_capture_timestamp_local",
    "source_capture_provenance",
    "no_market_action_guidance",
    "operator_review_only",
    "no_trading_authority",
    "no_queue_authority",
    "no_runtime_authority",
    "no_wallet_or_order_authority",
}


class ManualResolutionSourceCaptureSchemaTests(unittest.TestCase):
    def test_capture_schema_exists_parses_and_contains_required_fields(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

        self.assertEqual(schema["schema_version"], "manual_resolution_source_capture_schema.v1")
        self.assertEqual(schema["contract_version"], "manual_resolution_source_capture.v1")
        self.assertTrue(REQUIRED_FIELDS.issubset(set(schema["field_order"])))
        self.assertTrue(REQUIRED_FIELDS.issubset(set(schema["field_definitions"])))
        self.assertEqual(
            schema["capture_status_values"],
            ["not_started", "draft", "ready_for_local_review", "reviewed", "needs_revision"],
        )

    def test_high_completeness_and_review_recommended_fields_are_marked(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        definitions = schema["field_definitions"]

        for field in (
            "full_market_resolution_criteria_text",
            "full_resolution_rules",
            "official_source_references",
            "official_source_urls_or_rule_references",
        ):
            self.assertTrue(definitions[field]["required_for_high_completeness"])
            self.assertTrue(definitions[field]["may_be_empty_in_not_started_template"])

        self.assertTrue(
            definitions["source_reliability_review"][
                "recommended_before_openrouter_review"
            ]
        )
        self.assertTrue(
            definitions["reviewed_local_evidence_references"][
                "recommended_before_openrouter_review"
            ]
        )

    def test_schema_is_operator_review_only_with_no_authority_flags(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

        self.assertTrue(schema["no_market_action_guidance"])
        self.assertTrue(schema["operator_review_only"])
        self.assertTrue(schema["no_trading_authority"])
        self.assertTrue(schema["no_queue_authority"])
        self.assertTrue(schema["no_runtime_authority"])
        self.assertTrue(schema["no_wallet_or_order_authority"])
        self.assertEqual(schema["safety_summary"]["openrouter_calls_performed"], 0)
        self.assertEqual(schema["safety_summary"]["polymarket_api_calls_performed"], 0)
        self.assertEqual(schema["safety_summary"]["external_network_calls_performed"], 0)
        self.assertFalse(schema["safety_summary"]["api_key_accessed"])


if __name__ == "__main__":
    unittest.main()
