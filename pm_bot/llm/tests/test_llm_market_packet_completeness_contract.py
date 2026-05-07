import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "llm" / "source_evidence_enrichment_artifacts.py"
CONTRACT_JSON = ROOT / "pm_bot" / "llm" / "llm_market_packet_completeness_contract.v1.json"


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


class LlmMarketPacketCompletenessContractTests(unittest.TestCase):
    def test_contract_defines_batch_eligibility_and_high_completeness(self):
        _run_write()
        contract = _load_json(CONTRACT_JSON)

        self.assertEqual(contract["contract_version"], "llm_market_packet_completeness_contract.v1")
        self.assertIn("market_id", contract["required_fields"])
        self.assertIn("market_title_or_question", contract["minimum_for_batch_eligibility"])
        self.assertIn("category", contract["minimum_for_batch_eligibility"])
        self.assertIn("local_packet_provenance", contract["minimum_for_batch_eligibility"])
        self.assertIn("full_market_resolution_criteria_text", contract["minimum_for_high_evidence_completeness"])
        self.assertIn("operator_checklist", contract["minimum_for_high_evidence_completeness"])
        self.assertTrue(contract["category_specific_fields"])

    def test_contract_blocks_authority_and_market_action_content(self):
        _run_write()
        contract = _load_json(CONTRACT_JSON)
        blocked = set(contract["blocked_conditions"])
        safety = contract["no_authority_safety_constraints"]

        self.assertIn("runtime_trading_queue_wallet_or_dispatcher_authority_present", blocked)
        self.assertIn("market_action_guidance_present", blocked)
        self.assertIn("probability_ev_edge_confidence_or_side_selection_present", blocked)
        self.assertTrue(safety["operator_review_only"])
        self.assertTrue(safety["no_trading_authority"])
        self.assertTrue(safety["no_queue_authority"])
        self.assertTrue(safety["no_runtime_authority"])
        self.assertTrue(safety["no_wallet_or_order_authority"])
        self.assertEqual(contract["openrouter_calls_performed"], 0)
        self.assertEqual(contract["polymarket_api_calls_performed"], 0)
        self.assertEqual(contract["network_calls_performed"], 0)


if __name__ == "__main__":
    unittest.main()
