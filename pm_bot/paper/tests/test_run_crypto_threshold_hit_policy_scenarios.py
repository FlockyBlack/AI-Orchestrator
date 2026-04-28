import ast
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_threshold_hit_policy_scenarios.py"
SCENARIOS = ROOT / "pm_bot" / "paper" / "threshold_hit_policy_scenarios.v1.json"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_crypto_threshold_hit_policy_scenarios.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_crypto_threshold_hit_policy_scenarios.v1.md"
REFERENCE_CONTEXT = ROOT / "pm_bot" / "paper" / "threshold_hit_reference_context.v1.json"
DECISION_POLICY = ROOT / "pm_bot" / "paper" / "threshold_hit_decision_policy.v1.json"
REAL_SOURCE = ROOT / "local_snapshots" / "polymarket_markets_active_500_001.json"
THRESHOLD_REVIEW_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_threshold_hit_review_table.py"
THRESHOLD_TRIAGE_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_threshold_hit_triage_report.py"
REAL_TRIAGE_RUNNER = ROOT / "pm_bot" / "paper" / "run_real_market_triage_report.py"
OPERATOR_CYCLE_RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_paper_operator_cycle.py"
LIFECYCLE_GATES_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_regression_gates.py"

REQUIRED_POLICY_REASONS = {
    "before_event_requires_event_model",
    "deadline_not_future",
    "deadline_too_near",
    "liquidity_below_conservative_minimum",
    "missing_deadline",
    "missing_liquidity",
    "missing_reference_price",
    "missing_yes_price",
    "paper_candidates_disabled_by_policy",
    "target_distance_above_watchlist_limit",
    "target_distance_unavailable",
    "yes_price_above_conservative_limit",
}


def _run_json(*args):
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown(*args):
    return subprocess.run([sys.executable, str(RUNNER), "--markdown", *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _utf8_env():
    return {**os.environ, "PYTHONIOENCODING": "utf-8"}


class RunCryptoThresholdHitPolicyScenariosTests(unittest.TestCase):
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

    def test_scenarios_argument_accepts_default_fixture_path(self):
        default_payload = json.loads(_run_json().stdout)
        explicit_payload = json.loads(_run_json("--scenarios", str(SCENARIOS)).stdout)
        explicit_payload["scenario_fixture_path"] = default_payload["scenario_fixture_path"]
        self.assertEqual(explicit_payload, default_payload)

    def test_every_policy_reason_is_exercised(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(set(payload["summary"]["policy_reason_counts"]), REQUIRED_POLICY_REASONS)
        for reason in REQUIRED_POLICY_REASONS:
            self.assertGreater(payload["summary"]["policy_reason_counts"][reason], 0)

    def test_all_expected_scenario_decisions_pass(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["summary"]["all_expected_decisions_passed"])
        self.assertTrue(payload["summary"]["all_expected_results_passed"])
        self.assertTrue(all(row["result"] == "pass" for row in payload["scenarios"]))
        self.assertTrue(all(row["actual_decision"] == row["expected_decision"] for row in payload["scenarios"]))
        self.assertIn("triage_rejected", {row["actual_decision"] for row in payload["scenarios"]})

    def test_paper_orders_remain_zero(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["summary"]["paper_candidate_count"], 0)
        self.assertEqual(payload["summary"]["paper_orders_created"], 0)
        self.assertNotIn("paper_orders", payload)

    def test_summary_counts(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(
            payload["summary"],
            {
                "scenario_count": 12,
                "reviewed_candidates": 11,
                "no_action_count": 1,
                "watchlist_count": 2,
                "policy_blocked_count": 8,
                "paper_candidate_count": 0,
                "paper_orders_created": 0,
                "policy_reason_counts": {
                    "before_event_requires_event_model": 1,
                    "deadline_not_future": 1,
                    "deadline_too_near": 1,
                    "liquidity_below_conservative_minimum": 1,
                    "missing_deadline": 1,
                    "missing_liquidity": 1,
                    "missing_reference_price": 1,
                    "missing_yes_price": 1,
                    "paper_candidates_disabled_by_policy": 11,
                    "target_distance_above_watchlist_limit": 1,
                    "target_distance_unavailable": 1,
                    "yes_price_above_conservative_limit": 1,
                },
                "all_expected_decisions_passed": True,
                "all_expected_results_passed": True,
                "safety_flags": payload["safety_flags"],
            },
        )

    def test_existing_threshold_hit_review_table_still_passes(self):
        result = subprocess.run(
            [
                sys.executable,
                str(THRESHOLD_REVIEW_RUNNER),
                "--reference-context",
                str(REFERENCE_CONTEXT),
                "--decision-policy",
                str(DECISION_POLICY),
                "--markdown",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("- Threshold-hit candidates: 3", result.stdout)
        self.assertIn("- Policy blocked: 1", result.stdout)
        self.assertIn("- Paper candidates: 0", result.stdout)

    def test_threshold_hit_triage_still_passes(self):
        result = subprocess.run(
            [sys.executable, str(THRESHOLD_TRIAGE_RUNNER), "--source", str(REAL_SOURCE), "--markdown"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("- Threshold-hit crypto candidates found: 3", result.stdout)
        self.assertIn("- Supported triage candidates: 3", result.stdout)

    def test_real_market_triage_operator_and_lifecycle_still_pass(self):
        real_triage = subprocess.run(
            [sys.executable, str(REAL_TRIAGE_RUNNER), "--source", str(REAL_SOURCE), "--markdown"],
            cwd=ROOT,
            env=_utf8_env(),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("# Real Market Triage Report", real_triage.stdout)
        operator = json.loads(subprocess.run(
            [sys.executable, str(OPERATOR_CYCLE_RUNNER)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout)
        gates = json.loads(subprocess.run(
            [sys.executable, str(LIFECYCLE_GATES_RUNNER)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout)
        self.assertTrue(operator["safety_flags"]["offline_only"])
        self.assertEqual(gates["status"], "passed")

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

    def test_standard_library_only(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
