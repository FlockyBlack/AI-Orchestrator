import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AUDIT_JSON = ROOT / "pm_bot" / "llm" / "openrouter_operator_review_contour_046_053_audit.v1.json"
AUDIT_MD = ROOT / "pm_bot" / "llm" / "openrouter_operator_review_contour_046_053_audit.v1.md"


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class OpenrouterOperatorReviewContourAuditTests(unittest.TestCase):
    def test_contour_audit_exists_and_reports_required_combined_values(self):
        audit = _load_json(AUDIT_JSON)

        self.assertTrue(AUDIT_MD.exists())
        self.assertEqual(audit["schema_version"], "openrouter_operator_review_contour_046_053_audit.v1")
        self.assertEqual(audit["status"], "contour_audit_created")
        self.assertEqual(len(audit["tasks_covered"]), 8)
        self.assertEqual(audit["n3_summary"]["market_ids"], ["569333", "569334", "569343"])
        self.assertEqual(audit["n3_summary"]["calls"], 3)
        self.assertEqual(audit["n3_summary"]["cost"], 0.125982)
        self.assertEqual(audit["n3_summary"]["total_tokens"], 18686)
        self.assertEqual(audit["n3_summary"]["accepted_for_operator_review_count"], 3)
        self.assertEqual(audit["n3_summary"]["blocked_count"], 0)
        self.assertEqual(
            audit["n5_summary"]["market_ids"],
            ["569344", "569366", "569368", "569373", "573656"],
        )
        self.assertEqual(audit["n5_summary"]["calls"], 5)
        self.assertEqual(audit["n5_summary"]["cost"], 0.199089)
        self.assertEqual(audit["n5_summary"]["total_tokens"], 29887)
        self.assertEqual(audit["n5_summary"]["accepted_for_operator_review_count"], 5)
        self.assertEqual(audit["n5_summary"]["blocked_count"], 0)

        combined = audit["combined_summary"]
        self.assertEqual(combined["total_markets_successfully_reviewed"], 8)
        self.assertEqual(combined["total_openrouter_calls_in_successful_batches"], 8)
        self.assertEqual(combined["combined_cost"], 0.325071)
        self.assertEqual(combined["combined_tokens"], 48573)
        self.assertEqual(combined["total_blocked_in_successful_batches"], 0)
        self.assertEqual(combined["average_cost_per_market_combined"], 0.040633875)
        self.assertEqual(combined["average_tokens_per_market_combined"], 6071.625)

    def test_contour_audit_records_normalization_and_safety(self):
        audit = _load_json(AUDIT_JSON)

        self.assertTrue(audit["normalization"]["n3_all_fenced"])
        self.assertTrue(audit["normalization"]["n5_all_fenced"])
        self.assertEqual(audit["normalization"]["clean_raw_json_response_count_across_successful_batches"], 0)
        self.assertEqual(audit["normalization"]["policy"], "fenced_json_normalization.v1")
        self.assertTrue(audit["normalization"]["current_route_requires_fenced_json_normalization_v1"])

        safety = audit["safety"]
        self.assertTrue(safety["no_trading_authority"])
        self.assertTrue(safety["no_queue_authority"])
        self.assertTrue(safety["no_runtime_authority"])
        self.assertTrue(safety["no_dispatcher_authority"])
        self.assertTrue(safety["no_wallet_or_order_authority"])
        self.assertTrue(safety["no_polymarket_api_calls_in_openrouter_live_batch_tasks"])
        self.assertTrue(safety["api_key_not_leaked"])
        self.assertTrue(safety["operator_review_only"])
        self.assertTrue(safety["acceptance_is_not_trading_approval"])

    def test_contour_audit_artifact_paths_are_repo_relative_and_exist(self):
        audit = _load_json(AUDIT_JSON)
        for path in audit["artifact_pointers"].values():
            self.assertFalse(Path(path).is_absolute())
            self.assertTrue((ROOT / path).exists(), path)


if __name__ == "__main__":
    unittest.main()
