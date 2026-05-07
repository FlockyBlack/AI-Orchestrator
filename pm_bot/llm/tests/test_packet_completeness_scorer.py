import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class PacketCompletenessScorerTests(unittest.TestCase):
    def test_scorer_module_imports_and_loads_source_artifacts(self):
        scorer = importlib.import_module("pm_bot.llm.packet_completeness_scorer")

        inventory = scorer.load_inventory(root=ROOT)
        readiness = scorer.load_readiness_scores(root=ROOT)
        contract = scorer.load_completeness_contract(root=ROOT)

        self.assertEqual(len(inventory["markets"]), 14)
        self.assertEqual(len(readiness["markets"]), 14)
        self.assertEqual(
            contract["contract_version"],
            "llm_market_packet_completeness_contract.v1",
        )

    def test_summary_represents_all_source_001_markets_with_valid_scores_and_bands(self):
        scorer = importlib.import_module("pm_bot.llm.packet_completeness_scorer")
        inventory = scorer.load_inventory(root=ROOT)
        readiness = scorer.load_readiness_scores(root=ROOT)
        summary = scorer.summarize_packet_readiness(
            inventory=inventory,
            readiness_scores=readiness,
            root=ROOT,
        )

        inventory_ids = {item["market_id"] for item in inventory["markets"]}
        scored_ids = {item["market_id"] for item in summary["per_market_readiness"]}
        self.assertEqual(scored_ids, inventory_ids)
        self.assertEqual(summary["total_markets"], 14)
        self.assertEqual(
            summary["total_markets"],
            summary["high_count"]
            + summary["medium_count"]
            + summary["low_count"]
            + summary["blocked_count"],
        )

        allowed_bands = {"high", "medium", "low", "blocked"}
        for item in summary["per_market_readiness"]:
            self.assertGreaterEqual(item["current_score"], 0)
            self.assertLessEqual(item["current_score"], 100)
            self.assertIn(item["readiness_band"], allowed_bands)
            self.assertTrue(item["packet_exists"])
            self.assertTrue(item["prompt_exists"])
            self.assertTrue(item["no_market_action_guidance"])
            self.assertTrue(item["no_probability_ev_edge_confidence_side_selection"])

    def test_low_readiness_markets_need_local_enrichment_before_future_batch(self):
        scorer = importlib.import_module("pm_bot.llm.packet_completeness_scorer")
        summary = scorer.summarize_packet_readiness(root=ROOT)

        self.assertEqual(summary["high_count"], 0)
        self.assertEqual(summary["medium_count"], 10)
        self.assertEqual(summary["low_count"], 4)
        self.assertEqual(summary["blocked_count"], 0)
        self.assertEqual(
            summary["low_readiness_market_ids"],
            ["597964", "598936", "691547", "692258"],
        )
        low_markets = [
            item
            for item in summary["per_market_readiness"]
            if item["readiness_band"] == "low"
        ]
        self.assertTrue(
            all(
                item["needs_local_enrichment_before_future_openrouter_batch"]
                for item in low_markets
            )
        )
        self.assertTrue(
            all(not item["suitable_for_future_openrouter_batch"] for item in low_markets)
        )

    def test_scorer_safety_flags_deny_live_runtime_queue_and_trading_authority(self):
        scorer = importlib.import_module("pm_bot.llm.packet_completeness_scorer")
        summary = scorer.summarize_packet_readiness(root=ROOT)
        safety = summary["safety_flags"]

        self.assertTrue(safety["local_only"])
        self.assertTrue(safety["no_live_calls"])
        self.assertTrue(safety["operator_review_only"])
        self.assertTrue(safety["passive_context_only"])
        self.assertTrue(safety["no_trading_authority"])
        self.assertTrue(safety["no_queue_authority"])
        self.assertTrue(safety["no_runtime_authority"])
        self.assertTrue(safety["no_wallet_or_order_authority"])
        self.assertTrue(safety["no_market_action_guidance"])
        self.assertEqual(summary["openrouter_calls_performed"], 0)
        self.assertEqual(summary["polymarket_api_calls_performed"], 0)
        self.assertEqual(summary["external_network_calls_performed"], 0)


if __name__ == "__main__":
    unittest.main()
