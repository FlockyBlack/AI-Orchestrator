import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "llm" / "source_evidence_enrichment_artifacts.py"
DESIGN_JSON = ROOT / "pm_bot" / "llm" / "source_evidence_enrichment_design.v1.json"
DESIGN_MD = ROOT / "docs" / "PMBOT_SOURCE_EVIDENCE_ENRICHMENT_DESIGN.md"


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


class SourceEvidenceEnrichmentDesignTests(unittest.TestCase):
    def test_design_artifact_is_design_only_with_expected_adapters(self):
        _run_write()
        design = _load_json(DESIGN_JSON)
        adapter_names = {item["name"] for item in design["adapters"]}

        self.assertTrue(DESIGN_MD.exists())
        self.assertEqual(design["implementation_status"], "design_only")
        self.assertFalse(design["live_adapters_implemented"])
        self.assertFalse(design["runtime_wiring_added"])
        self.assertFalse(design["network_code_added"])
        for expected_name in (
            "resolution_source_extractor_local",
            "category_field_normalizer",
            "packet_completeness_scorer",
            "source_gap_normalizer",
            "contradiction_context_builder",
            "operator_checklist_standardizer",
            "local_snapshot_evidence_reader",
            "future_read_only_polymarket_gamma_snapshot_importer",
            "future_category_specific_source_adapter",
        ):
            self.assertIn(expected_name, adapter_names)

    def test_design_contains_no_live_network_implementation(self):
        _run_write()
        design = _load_json(DESIGN_JSON)

        self.assertEqual(design["openrouter_calls_performed"], 0)
        self.assertEqual(design["polymarket_api_calls_performed"], 0)
        self.assertEqual(design["network_calls_performed"], 0)
        for adapter in design["adapters"]:
            self.assertEqual(adapter["current_implementation_status"], "design_only")
            self.assertFalse(adapter["requires_network"])
            self.assertTrue(adapter["safety_constraints"]["operator_review_only"])
            self.assertTrue(adapter["safety_constraints"]["no_market_action_guidance"])


if __name__ == "__main__":
    unittest.main()
