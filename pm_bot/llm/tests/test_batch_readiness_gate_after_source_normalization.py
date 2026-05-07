import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GATE = (
    ROOT
    / "pm_bot"
    / "llm"
    / "current_llm_batch_readiness_gate_after_source_normalization.v1.json"
)


class BatchReadinessGateAfterSourceNormalizationTests(unittest.TestCase):
    def test_gate_exists_parses_and_keeps_batch_passive(self):
        gate = json.loads(GATE.read_text(encoding="utf-8"))

        self.assertEqual(
            gate["schema_version"],
            "current_llm_batch_readiness_gate_after_source_normalization.v1",
        )
        self.assertEqual(
            gate["status"],
            "batch_readiness_gate_after_source_normalization_created",
        )
        self.assertEqual(gate["total_markets"], 14)
        self.assertEqual(gate["high_count"], 0)
        self.assertEqual(gate["medium_count"], 10)
        self.assertEqual(gate["low_count"], 4)
        self.assertEqual(gate["blocked_count"], 0)
        self.assertEqual(gate["eligible_for_future_llm_review_count"], 10)
        self.assertEqual(gate["eligible_for_future_openrouter_batch_count"], 10)
        self.assertEqual(gate["needs_local_enrichment_count"], 14)
        self.assertEqual(len(gate["markets_still_missing_resolution_sources"]), 14)
        self.assertEqual(
            gate["blocked_or_low_readiness_markets"],
            ["597964", "598936", "691547", "692258"],
        )
        self.assertFalse(gate["future_live_batch_scheduled"])
        self.assertFalse(gate["future_openrouter_batch_approved"])
        self.assertFalse(gate["future_llm_review_approved"])

    def test_gate_contains_no_trading_queue_runtime_or_live_authority(self):
        gate = json.loads(GATE.read_text(encoding="utf-8"))
        safety = gate["safety_flags"]

        self.assertTrue(safety["local_only"])
        self.assertTrue(safety["operator_review_only"])
        self.assertTrue(safety["passive_context_only"])
        self.assertTrue(safety["no_live_calls"])
        self.assertTrue(safety["no_trading_authority"])
        self.assertTrue(safety["no_queue_authority"])
        self.assertTrue(safety["no_runtime_authority"])
        self.assertTrue(safety["no_dispatcher_authority"])
        self.assertTrue(safety["no_wallet_or_order_authority"])
        self.assertTrue(safety["no_market_action_guidance"])
        self.assertEqual(gate["openrouter_calls_performed"], 0)
        self.assertEqual(gate["polymarket_api_calls_performed"], 0)
        self.assertEqual(gate["external_network_calls_performed"], 0)


if __name__ == "__main__":
    unittest.main()
