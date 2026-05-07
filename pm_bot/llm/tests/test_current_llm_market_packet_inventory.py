import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INVENTORY_JSON = ROOT / "pm_bot" / "llm" / "current_llm_market_packet_inventory.v1.json"
INVENTORY_MD = ROOT / "pm_bot" / "llm" / "current_llm_market_packet_inventory.v1.md"

EXPECTED_REQUIRED_MARKET_IDS = {
    "563650",
    "569332",
    "569333",
    "569334",
    "569343",
    "569344",
    "569366",
    "569368",
    "569373",
    "573656",
}


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class CurrentLlmMarketPacketInventoryTests(unittest.TestCase):
    def test_inventory_exists_and_contains_known_market_ids(self):
        inventory = _load_json(INVENTORY_JSON)
        market_ids = {item["market_id"] for item in inventory["markets"]}

        self.assertTrue(INVENTORY_MD.exists())
        self.assertEqual(inventory["schema_version"], "current_llm_market_packet_inventory.v1")
        self.assertEqual(inventory["status"], "market_packet_inventory_created")
        self.assertTrue(EXPECTED_REQUIRED_MARKET_IDS.issubset(market_ids))
        self.assertEqual(inventory["aggregate"]["total_markets_found"], 14)
        self.assertEqual(inventory["aggregate"]["total_with_packet"], 14)
        self.assertEqual(inventory["aggregate"]["total_with_prompt"], 14)
        self.assertEqual(inventory["aggregate"]["total_reviewed_by_openrouter"], 10)
        self.assertEqual(inventory["aggregate"]["total_accepted_for_operator_review"], 10)

    def test_inventory_categories_are_local_and_deterministic(self):
        inventory = _load_json(INVENTORY_JSON)
        by_market = {item["market_id"]: item for item in inventory["markets"]}

        self.assertEqual(by_market["563650"]["category"], "legal/courts")
        self.assertEqual(by_market["569333"]["category"], "elections")
        self.assertEqual(by_market["573656"]["category"], "crypto")
        self.assertEqual(by_market["597964"]["category"], "politics")
        self.assertEqual(by_market["691547"]["category"], "company/business")
        self.assertEqual(inventory["aggregate"]["unknown_category_count"], 0)
        self.assertEqual(inventory["aggregate"]["category_counts"]["elections"], 9)
        self.assertEqual(inventory["aggregate"]["category_counts"]["company/business"], 2)

    def test_inventory_entries_have_repo_relative_paths_and_review_statuses(self):
        inventory = _load_json(INVENTORY_JSON)

        for item in inventory["markets"]:
            self.assertFalse(Path(item["packet_file_path"]).is_absolute())
            self.assertTrue((ROOT / item["packet_file_path"]).exists(), item["packet_file_path"])
            self.assertFalse(Path(item["prompt_file_path"]).is_absolute())
            self.assertTrue((ROOT / item["prompt_file_path"]).exists(), item["prompt_file_path"])
            self.assertEqual(item["source_artifact_family"], "manual_packet_batch")
            self.assertIn(item["category_confidence"], {"high", "medium", "low", "unknown"})
            self.assertIs(item["resolution_source_fields_present"], True)
            self.assertIs(item["local_evidence_fields_present"], True)
            self.assertIs(item["missing_evidence_notes_present"], True)
            self.assertIs(item["eligible_for_llm_review"], True)

        reviewed = {item["market_id"]: item for item in inventory["markets"] if item["already_reviewed_by_openrouter"]}
        self.assertEqual(set(reviewed), EXPECTED_REQUIRED_MARKET_IDS)
        self.assertEqual(reviewed["563650"]["batch_or_task_where_reviewed"], "028")
        self.assertEqual(reviewed["569332"]["batch_or_task_where_reviewed"], "033")
        self.assertEqual(reviewed["569333"]["batch_or_task_where_reviewed"], "046")
        self.assertEqual(reviewed["569344"]["batch_or_task_where_reviewed"], "051")
        self.assertTrue(all(item["accepted_for_operator_review"] is True for item in reviewed.values()))

    def test_inventory_aggregate_missing_lists_are_deterministic(self):
        inventory = _load_json(INVENTORY_JSON)
        aggregate = inventory["aggregate"]

        self.assertEqual(len(aggregate["markets_missing_resolution_source"]), 14)
        self.assertEqual(len(aggregate["markets_missing_local_evidence"]), 14)
        self.assertEqual(len(aggregate["markets_with_low_packet_completeness"]), 14)
        self.assertIn("resolution rules", aggregate["recommendation_for_next_local_enrichment_step"])

    def test_inventory_safety_counters_are_zero(self):
        inventory = _load_json(INVENTORY_JSON)

        self.assertEqual(inventory["network_calls_performed"], 0)
        self.assertEqual(inventory["polymarket_api_calls_performed"], 0)
        self.assertEqual(inventory["openrouter_calls_performed"], 0)
        self.assertFalse(inventory["safety_summary"]["api_key_accessed"])


if __name__ == "__main__":
    unittest.main()
