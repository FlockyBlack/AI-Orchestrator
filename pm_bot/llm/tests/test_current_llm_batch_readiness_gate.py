import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "llm" / "export_packet_completeness_readiness.py"
GATE_JSON = ROOT / "pm_bot" / "llm" / "current_llm_batch_readiness_gate.v1.json"
GATE_MD = ROOT / "pm_bot" / "llm" / "current_llm_batch_readiness_gate.v1.md"


def _frag(*parts):
    return "".join(parts)


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


class CurrentLlmBatchReadinessGateTests(unittest.TestCase):
    def test_gate_export_writes_parseable_json_and_markdown(self):
        result = json.loads(_run_write().stdout)
        gate = _load_json(GATE_JSON)

        self.assertEqual(result["status"], "batch_readiness_gate_written")
        self.assertTrue(GATE_JSON.exists())
        self.assertTrue(GATE_MD.exists())
        self.assertEqual(gate["gate_version"], "current_llm_batch_readiness_gate.v1")
        self.assertEqual(gate["status"], "batch_readiness_gate_created")
        self.assertEqual(
            gate["generated_from"]["current_llm_market_packet_inventory"],
            "pm_bot/llm/current_llm_market_packet_inventory.v1.json",
        )
        self.assertEqual(
            gate["generated_from"]["current_llm_packet_evidence_readiness_scores"],
            "pm_bot/llm/current_llm_packet_evidence_readiness_scores.v1.json",
        )
        self.assertEqual(
            gate["generated_from"]["llm_market_packet_completeness_contract"],
            "pm_bot/llm/llm_market_packet_completeness_contract.v1.json",
        )

    def test_gate_totals_match_inventory_and_source_001_readiness_counts(self):
        _run_write()
        gate = _load_json(GATE_JSON)

        self.assertEqual(gate["total_markets"], 14)
        self.assertEqual(gate["high_count"], 0)
        self.assertEqual(gate["medium_count"], 10)
        self.assertEqual(gate["low_count"], 4)
        self.assertEqual(gate["blocked_count"], 0)
        self.assertEqual(
            gate["total_markets"],
            gate["high_count"]
            + gate["medium_count"]
            + gate["low_count"]
            + gate["blocked_count"],
        )
        self.assertEqual(gate["reviewed_count"], 10)
        self.assertEqual(gate["unreviewed_count"], 4)
        self.assertEqual(gate["eligible_for_future_llm_review_count"], 10)
        self.assertEqual(gate["eligible_for_future_openrouter_batch_count"], 10)
        self.assertEqual(gate["needs_local_enrichment_count"], 14)
        self.assertEqual(
            gate["needs_local_enrichment_before_future_openrouter_batch_count"],
            4,
        )

    def test_gate_marks_low_readiness_markets_as_needing_local_enrichment_first(self):
        _run_write()
        gate = _load_json(GATE_JSON)
        low_ids = ["597964", "598936", "691547", "692258"]

        self.assertEqual(gate["low_readiness_market_ids"], low_ids)
        self.assertEqual(
            gate["needs_local_enrichment_before_future_openrouter_batch_market_ids"],
            low_ids,
        )
        by_market = {item["market_id"]: item for item in gate["per_market_readiness"]}
        for market_id in low_ids:
            item = by_market[market_id]
            self.assertEqual(item["readiness_band"], "low")
            self.assertTrue(item["needs_local_enrichment_before_review"])
            self.assertTrue(item["needs_local_enrichment_before_future_openrouter_batch"])
            self.assertFalse(item["suitable_for_future_openrouter_batch"])

    def test_gate_does_not_approve_live_calls_or_authority(self):
        _run_write()
        gate = _load_json(GATE_JSON)
        safety = gate["safety_flags"]

        self.assertFalse(gate["future_live_batch_scheduled"])
        self.assertFalse(gate["future_openrouter_batch_approved"])
        self.assertFalse(gate["future_llm_review_approved"])
        self.assertTrue(safety["local_only"])
        self.assertTrue(safety["no_live_calls"])
        self.assertTrue(safety["no_trading_authority"])
        self.assertTrue(safety["no_queue_authority"])
        self.assertTrue(safety["no_runtime_authority"])
        self.assertTrue(safety["no_dispatcher_authority"])
        self.assertTrue(safety["no_wallet_or_order_authority"])
        self.assertTrue(safety["operator_review_only"])
        self.assertTrue(safety["no_market_action_guidance"])
        self.assertEqual(gate["openrouter_calls_performed"], 0)
        self.assertEqual(gate["polymarket_api_calls_performed"], 0)
        self.assertEqual(gate["external_network_calls_performed"], 0)
        self.assertEqual(gate["network_calls_performed"], 0)

    def test_gate_public_markdown_contains_no_market_action_recommendations(self):
        _run_write()
        text = GATE_MD.read_text(encoding="utf-8").lower()
        forbidden_phrases = [
            "buy recommendation",
            "sell recommendation",
            "hold recommendation",
            "enter recommendation",
            "exit recommendation",
            "market action recommendation",
            "side recommendation",
        ]
        for phrase in forbidden_phrases:
            self.assertNotIn(phrase, text)
        self.assertNotIn(_frag("openrouter", "_api", "_key").lower(), text)


if __name__ == "__main__":
    unittest.main()
