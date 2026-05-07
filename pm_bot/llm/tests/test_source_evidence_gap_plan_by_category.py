import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "llm" / "source_evidence_enrichment_artifacts.py"
INVENTORY_JSON = ROOT / "pm_bot" / "llm" / "current_llm_market_packet_inventory.v1.json"
GAP_PLAN_JSON = ROOT / "pm_bot" / "llm" / "source_evidence_gap_plan_by_category.v1.json"


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


class SourceEvidenceGapPlanByCategoryTests(unittest.TestCase):
    def test_gap_plan_includes_every_inventory_category(self):
        _run_write()
        inventory = _load_json(INVENTORY_JSON)
        plan = _load_json(GAP_PLAN_JSON)
        inventory_categories = {item["category"] for item in inventory["markets"]}
        plan_categories = {item["category"] for item in plan["categories"]}

        self.assertEqual(plan_categories, inventory_categories)
        self.assertEqual(plan["category_count"], len(inventory_categories))
        for category in plan["categories"]:
            self.assertTrue(category["market_ids_in_category"])
            self.assertTrue(category["common_missing_fields"])
            self.assertTrue(category["common_medium-completeness_causes"])
            self.assertTrue(category["required_local_enrichment_fields_to_reach_high"])
            self.assertIn(category["recommended_priority"], {"high", "medium", "low"})
            self.assertIn(category["estimated_effort"], {"small", "medium", "large"})

    def test_gap_plan_is_planning_only_and_disallows_live_actions(self):
        _run_write()
        plan = _load_json(GAP_PLAN_JSON)

        self.assertEqual(plan["openrouter_calls_performed"], 0)
        self.assertEqual(plan["polymarket_api_calls_performed"], 0)
        self.assertEqual(plan["network_calls_performed"], 0)
        for category in plan["categories"]:
            disallowed = set(category["unsafe_or_disallowed_sources/actions"])
            self.assertIn("do_not_fetch_external_data", disallowed)
            self.assertIn("do_not_call_polymarket_api", disallowed)
            self.assertIn("do_not_call_openrouter_or_other_llm_api", disallowed)
            self.assertIn("do_not_mutate_queue_state", disallowed)


if __name__ == "__main__":
    unittest.main()
