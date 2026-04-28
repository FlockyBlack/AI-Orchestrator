import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "research" / "run_research_dossier_scenarios.py"
SCENARIOS = ROOT / "pm_bot" / "research" / "research_dossier_scenarios.v1.json"
EXPECTED_JSON = ROOT / "pm_bot" / "research" / "expected_research_dossier_scenarios.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "research" / "expected_research_dossier_scenarios.v1.md"
REQUIRED_SCENARIOS = {
    "missing_resolution_criteria",
    "weak_sources_only",
    "one_sided_low_reliability_sources",
    "conflicting_evidence",
    "stale_sources",
    "probability_range_overlaps_market_price",
    "strong_sources_but_missing_key_info",
    "strong_sources_clear_edge",
    "high_uncertainty_high_market_price",
    "operator_note_requires_manual_review",
}


def _frag(*parts):
    return "".join(parts)


def _run_json(*args):
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown(*args):
    return subprocess.run([sys.executable, str(RUNNER), "--markdown", *args], cwd=ROOT, capture_output=True, text=True, check=True)


class RunResearchDossierScenariosTests(unittest.TestCase):
    def test_json_output_is_deterministic_and_matches_expected(self):
        first = _run_json().stdout
        second = _run_json().stdout
        self.assertEqual(first, second)
        self.assertEqual(json.loads(first), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_is_deterministic_and_matches_expected(self):
        first = _run_markdown().stdout
        second = _run_markdown().stdout
        self.assertEqual(first, second)
        self.assertEqual(first, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_fixture_contract_contains_required_scenarios(self):
        payload = json.loads(SCENARIOS.read_text(encoding="utf-8"))
        scenario_ids = {scenario["scenario_id"] for scenario in payload["scenarios"]}
        self.assertEqual(scenario_ids, REQUIRED_SCENARIOS)
        self.assertTrue(payload["fixture_only"])
        self.assertTrue(payload["paper_only"])
        self.assertTrue(payload["local_only"])

    def test_summary_counts_and_expected_decisions_are_locked(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["scenario_count"], 10)
        self.assertEqual(payload["no_action_count"], 4)
        self.assertEqual(payload["watchlist_count"], 5)
        self.assertEqual(payload["paper_candidate_count"], 1)
        self.assertEqual(payload["paper_orders_created"], 0)
        self.assertTrue(payload["all_expected_decisions_passed"])
        self.assertTrue(payload["all_expected_reason_codes_present"])

    def test_required_decision_coverage_is_present(self):
        payload = json.loads(_run_json().stdout)
        decisions = {row["scenario_id"]: row["actual_decision"] for row in payload["scenario_results"]}
        self.assertEqual(decisions["missing_resolution_criteria"], "no_action")
        self.assertEqual(decisions["weak_sources_only"], "no_action")
        self.assertIn(decisions["one_sided_low_reliability_sources"], {"no_action", "watchlist"})
        self.assertEqual(decisions["conflicting_evidence"], "watchlist")
        self.assertIn(decisions["stale_sources"], {"no_action", "watchlist"})
        self.assertIn(decisions["probability_range_overlaps_market_price"], {"no_action", "watchlist"})
        self.assertEqual(decisions["strong_sources_but_missing_key_info"], "watchlist")
        self.assertEqual(decisions["strong_sources_clear_edge"], "paper_candidate")
        self.assertEqual(decisions["high_uncertainty_high_market_price"], "no_action")
        self.assertIn(decisions["operator_note_requires_manual_review"], {"no_action", "watchlist"})

    def test_scenario_results_create_no_orders_or_state(self):
        payload = json.loads(_run_json().stdout)
        for row in payload["scenario_results"]:
            self.assertEqual(row["paper_orders_created"], 0)
            self.assertFalse(row["workspace_state_written"])
            self.assertTrue(row["safety_flags"]["offline_only"])
            self.assertTrue(row["safety_flags"]["paper_only"])
            self.assertFalse(row["safety_flags"]["real_order_created"])
            self.assertFalse(row["safety_flags"]["trading_allowed"])

    def test_scenario_diagnostics_cover_stale_and_manual_review_notes(self):
        payload = json.loads(_run_json().stdout)
        rows = {row["scenario_id"]: row for row in payload["scenario_results"]}
        self.assertGreater(rows["stale_sources"]["scenario_flags"]["stale_source_count"], 0)
        self.assertTrue(rows["operator_note_requires_manual_review"]["scenario_flags"]["operator_note_requires_manual_review"])

    def test_custom_scenarios_option_accepts_local_fixture_path(self):
        fixture = json.loads(SCENARIOS.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "research_dossier_scenarios.json"
            path.write_text(json.dumps(fixture, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            payload = json.loads(_run_json("--scenarios", str(path)).stdout)
        self.assertEqual(payload["scenario_count"], 10)
        self.assertTrue(payload["all_expected_decisions_passed"])

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_json().stdout)
        flags = payload["safety_flags"]
        self.assertTrue(flags["offline_only"])
        self.assertTrue(flags["paper_only"])
        for key in (
            "live_fetcher_implemented",
            "api_used",
            "network_used",
            "wallet_used",
            "real_order_created",
            "trading_allowed",
            "runtime_wiring_changed",
            "dispatcher_touched",
            "prompt_automation_added",
        ):
            self.assertFalse(flags[key])

    def test_no_runtime_network_wallet_or_live_order_behavior(self):
        source = RUNNER.read_text(encoding="utf-8").lower()
        forbidden = [
            _frag("re", "quests"),
            _frag("urllib", ".", "request"),
            "socket",
            _frag("run", "_", "codex"),
            _frag("private", "_", "key"),
            _frag("submit", "_", "order"),
            _frag("execute", "_", "trade"),
        ]
        for term in forbidden:
            self.assertNotIn(term, source)

    def test_standard_library_only(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "collections", "datetime", "importlib", "json", "pathlib", "sys"})


if __name__ == "__main__":
    unittest.main()
