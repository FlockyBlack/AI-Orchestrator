import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PLAN = ROOT / "pm_bot" / "llm" / "local_source_enrichment_action_plan.v1.json"


class LocalSourceEnrichmentActionPlanTests(unittest.TestCase):
    def test_action_plan_exists_and_is_passive_only(self):
        plan = json.loads(PLAN.read_text(encoding="utf-8"))

        self.assertEqual(plan["schema_version"], "local_source_enrichment_action_plan.v1")
        self.assertEqual(plan["status"], "local_source_enrichment_action_plan_created")
        self.assertEqual(plan["plan_type"], "passive_local_proposal_not_runtime_queue")
        self.assertEqual(len(plan["actions"]), 14)
        self.assertTrue(plan["passive_only"])
        self.assertFalse(plan["queue_mutation_performed"])
        self.assertFalse(plan["runtime_objects_created"])
        self.assertFalse(plan["dispatcher_integration_added"])
        self.assertEqual(plan["queue_items_created"], 0)
        self.assertFalse(plan["queue_state_mutated"])
        self.assertTrue(plan["no_market_action_guidance"])

    def test_per_market_actions_do_not_require_network_or_market_guidance(self):
        plan = json.loads(PLAN.read_text(encoding="utf-8"))

        for action in plan["actions"]:
            self.assertIn(action["priority"], {"high", "medium", "low"})
            self.assertFalse(action["requires_external_network"])
            self.assertTrue(action["future_read_only_network_possible_with_approval"])
            self.assertTrue(action["operator_manual_input_needed"])
            self.assertTrue(action["no_market_action_guidance"])
            self.assertIn("full_market_resolution_criteria_text", action["missing_fields"])
            self.assertFalse(Path(action["suggested_artifact_to_update_or_create"]).is_absolute())

        safety = plan["safety_flags"]
        self.assertTrue(safety["no_queue_authority"])
        self.assertTrue(safety["no_runtime_authority"])
        self.assertTrue(safety["no_dispatcher_authority"])
        self.assertTrue(safety["no_trading_authority"])
        self.assertEqual(plan["openrouter_calls_performed"], 0)
        self.assertEqual(plan["polymarket_api_calls_performed"], 0)
        self.assertEqual(plan["external_network_calls_performed"], 0)


if __name__ == "__main__":
    unittest.main()
