import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class ResolutionSourceNormalizerTests(unittest.TestCase):
    def test_normalizer_imports_and_loads_inventory(self):
        normalizer = importlib.import_module("pm_bot.llm.resolution_source_normalizer")
        inventory = normalizer.load_market_inventory(root=ROOT)

        self.assertEqual(len(inventory["markets"]), 14)
        self.assertTrue(hasattr(normalizer, "find_local_packet_artifacts"))
        self.assertTrue(hasattr(normalizer, "extract_resolution_source_fields"))
        self.assertTrue(hasattr(normalizer, "normalize_resolution_source_record"))

    def test_normalized_records_mark_missing_fields_explicitly(self):
        normalizer = importlib.import_module("pm_bot.llm.resolution_source_normalizer")
        inventory = normalizer.load_market_inventory(root=ROOT)
        records = [
            normalizer.normalize_resolution_source_record(market, root=ROOT)
            for market in inventory["markets"]
        ]

        self.assertEqual(len(records), 14)
        for record in records:
            self.assertIn("full_market_resolution_criteria_text", record)
            self.assertIn("full_resolution_rules", record)
            self.assertIn("official_source_urls_or_rule_references", record)
            self.assertIsInstance(record["missing_resolution_source_fields"], list)
            self.assertIn(
                "full_market_resolution_criteria_text",
                record["missing_resolution_source_fields"],
            )
            self.assertFalse(record["official_source_urls_or_rule_references_present"])
            self.assertEqual(record["official_source_urls_or_rule_references"], [])
            self.assertFalse(record["full_resolution_rules_present"])
            self.assertIsNone(record["full_resolution_rules"])
            self.assertTrue(record["no_market_action_guidance"])

    def test_summary_is_deterministic_for_all_inventory_markets(self):
        normalizer = importlib.import_module("pm_bot.llm.resolution_source_normalizer")
        first = normalizer.export_resolution_source_audit(root=ROOT)
        second = normalizer.export_resolution_source_audit(root=ROOT)

        self.assertEqual(first, second)
        inventory_ids = {
            item["market_id"]
            for item in normalizer.load_market_inventory(root=ROOT)["markets"]
        }
        audit_ids = {item["market_id"] for item in first["markets"]}
        self.assertEqual(audit_ids, inventory_ids)
        self.assertEqual(first["aggregate"]["total_markets_audited"], 14)
        self.assertEqual(first["aggregate"]["markets_missing_full_resolution_rules"], 14)
        self.assertEqual(first["openrouter_calls_performed"], 0)
        self.assertEqual(first["polymarket_api_calls_performed"], 0)
        self.assertEqual(first["external_network_calls_performed"], 0)


if __name__ == "__main__":
    unittest.main()
