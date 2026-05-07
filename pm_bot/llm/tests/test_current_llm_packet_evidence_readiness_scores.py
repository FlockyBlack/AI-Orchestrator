import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "llm" / "source_evidence_enrichment_artifacts.py"
INVENTORY_JSON = ROOT / "pm_bot" / "llm" / "current_llm_market_packet_inventory.v1.json"
READINESS_JSON = ROOT / "pm_bot" / "llm" / "current_llm_packet_evidence_readiness_scores.v1.json"


def _run_write():
    return subprocess.run(
        [sys.executable, str(RUNNER), "--write"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class CurrentLlmPacketEvidenceReadinessScoresTests(unittest.TestCase):
    def test_readiness_scores_include_all_inventory_market_ids_and_valid_bands(self):
        _run_write()
        inventory = _load_json(INVENTORY_JSON)
        readiness = _load_json(READINESS_JSON)
        inventory_ids = {item["market_id"] for item in inventory["markets"]}
        scored_ids = {item["market_id"] for item in readiness["markets"]}

        self.assertEqual(scored_ids, inventory_ids)
        self.assertEqual(len(scored_ids), 14)
        allowed_bands = {"high", "medium", "low", "blocked"}
        for item in readiness["markets"]:
            self.assertGreaterEqual(item["evidence_readiness_score"], 0)
            self.assertLessEqual(item["evidence_readiness_score"], 100)
            self.assertIn(item["readiness_band"], allowed_bands)
            self.assertTrue(item["no_market_action_guidance"])

    def test_score_summary_totals_match_market_count_and_reviewed_acceptance_is_not_high(self):
        _run_write()
        readiness = _load_json(READINESS_JSON)
        aggregate = readiness["aggregate"]

        self.assertEqual(aggregate["total_markets_scored"], 14)
        self.assertEqual(
            aggregate["total_markets_scored"],
            aggregate["high_count"]
            + aggregate["medium_count"]
            + aggregate["low_count"]
            + aggregate["blocked_count"],
        )
        self.assertEqual(aggregate["reviewed_count"], 10)
        self.assertEqual(aggregate["unreviewed_count"], 4)
        accepted = [
            item for item in readiness["markets"] if item["accepted_for_operator_review"] is True
        ]
        self.assertEqual(len(accepted), 10)
        self.assertTrue(all(item["readiness_band"] == "medium" for item in accepted))
        self.assertTrue(all(item["needs_local_enrichment_before_review"] for item in accepted))

    def test_scoring_model_is_evidence_only_not_trading_or_probability(self):
        _run_write()
        readiness = _load_json(READINESS_JSON)
        model = readiness["scoring_model"]

        self.assertEqual(model["score_scope"], "evidence_and_packet_readiness_only")
        self.assertTrue(model["not_market_attractiveness_score"])
        self.assertTrue(model["not_probability_score"])
        self.assertTrue(model["not_expected_value_score"])
        self.assertTrue(model["not_side_selection_score"])
        self.assertEqual(readiness["openrouter_calls_performed"], 0)
        self.assertEqual(readiness["polymarket_api_calls_performed"], 0)
        self.assertEqual(readiness["network_calls_performed"], 0)


if __name__ == "__main__":
    unittest.main()
