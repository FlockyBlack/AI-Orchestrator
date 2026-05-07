import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "llm" / "source_evidence_enrichment_artifacts.py"
INVENTORY_JSON = ROOT / "pm_bot" / "llm" / "current_llm_market_packet_inventory.v1.json"
REQUIREMENTS_JSON = ROOT / "pm_bot" / "llm" / "source_evidence_enrichment_requirements.v1.json"
REQUIREMENTS_MD = ROOT / "pm_bot" / "llm" / "source_evidence_enrichment_requirements.v1.md"


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


class SourceEvidenceEnrichmentRequirementsTests(unittest.TestCase):
    def test_requirements_artifact_exists_parses_and_covers_inventory_categories(self):
        result = json.loads(_run_write().stdout)
        inventory = _load_json(INVENTORY_JSON)
        requirements = _load_json(REQUIREMENTS_JSON)

        self.assertEqual(result["task_id"], "PMBOT-SOURCE-001-EVIDENCE-ENRICHMENT-DESIGN-FROM-INVENTORY")
        self.assertTrue(REQUIREMENTS_MD.exists())
        inventory_categories = {item["category"] for item in inventory["markets"]}
        requirement_categories = {item["category"] for item in requirements["categories"]}

        self.assertEqual(requirement_categories, inventory_categories)
        self.assertEqual(requirements["category_count"], len(inventory_categories))
        self.assertNotIn("unknown", requirement_categories)
        for item in requirements["categories"]:
            for key in (
                "required_core_fields",
                "recommended_context_fields",
                "resolution_source_requirements",
                "local_evidence_requirements",
                "contradiction_check_requirements",
                "risk_note_requirements",
                "operator_checklist_requirements",
                "minimum_packet_fields_for_llm_review",
                "fields_required_for_high_completeness",
                "fields_allowed_to_be_unknown",
                "local_only_enrichment_notes",
                "prohibited_enrichment_behavior",
            ):
                self.assertIn(key, item)
                self.assertTrue(item[key], key)

    def test_requirements_contain_no_market_action_guidance(self):
        _run_write()
        text = REQUIREMENTS_JSON.read_text(encoding="utf-8").lower()
        markdown = REQUIREMENTS_MD.read_text(encoding="utf-8").lower()
        forbidden_phrases = (
            "buy recommendation",
            "sell recommendation",
            "hold recommendation",
            "enter position",
            "exit position",
            "recommended side",
            "place an order",
            "submit an order",
        )
        for phrase in forbidden_phrases:
            self.assertNotIn(phrase, text)
            self.assertNotIn(phrase, markdown)
        self.assertTrue(_load_json(REQUIREMENTS_JSON)["safety_summary"]["no_market_action_guidance"])


if __name__ == "__main__":
    unittest.main()
