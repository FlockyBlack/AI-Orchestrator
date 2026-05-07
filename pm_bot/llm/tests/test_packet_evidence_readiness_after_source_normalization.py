import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCORES = (
    ROOT
    / "pm_bot"
    / "llm"
    / "current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.json"
)


class PacketEvidenceReadinessAfterSourceNormalizationTests(unittest.TestCase):
    def test_after_normalization_scores_cover_all_markets_with_valid_values(self):
        scores = json.loads(SCORES.read_text(encoding="utf-8"))

        self.assertEqual(
            scores["schema_version"],
            "current_llm_packet_evidence_readiness_scores_after_source_normalization.v1",
        )
        self.assertEqual(len(scores["markets"]), 14)
        allowed_bands = {"high", "medium", "low", "blocked"}
        for market in scores["markets"]:
            self.assertGreaterEqual(market["previous_score"], 0)
            self.assertLessEqual(market["previous_score"], 100)
            self.assertGreaterEqual(market["updated_score"], 0)
            self.assertLessEqual(market["updated_score"], 100)
            self.assertEqual(
                market["delta"],
                market["updated_score"] - market["previous_score"],
            )
            self.assertIn(market["previous_readiness_band"], allowed_bands)
            self.assertIn(market["updated_readiness_band"], allowed_bands)
            self.assertTrue(market["no_market_action_guidance"])

    def test_score_deltas_are_deterministic_and_evidence_only(self):
        scores = json.loads(SCORES.read_text(encoding="utf-8"))
        aggregate = scores["aggregate"]

        self.assertEqual(aggregate["previous_high_count"], 0)
        self.assertEqual(aggregate["updated_high_count"], 0)
        self.assertEqual(aggregate["previous_medium_count"], 10)
        self.assertEqual(aggregate["updated_medium_count"], 10)
        self.assertEqual(aggregate["previous_low_count"], 4)
        self.assertEqual(aggregate["updated_low_count"], 4)
        self.assertEqual(aggregate["markets_worsened"], [])
        self.assertIn("markets_with_source_fields_improved", aggregate)
        self.assertIn("full_market_resolution_criteria_text", {
            item["field"] for item in aggregate["remaining_top_missing_fields"]
        })
        self.assertTrue(scores["safety_flags"]["no_market_action_guidance"])
        self.assertTrue(scores["safety_flags"]["no_trading_authority"])
        self.assertEqual(scores["openrouter_calls_performed"], 0)
        self.assertEqual(scores["polymarket_api_calls_performed"], 0)
        self.assertEqual(scores["external_network_calls_performed"], 0)


if __name__ == "__main__":
    unittest.main()
