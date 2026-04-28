import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_series_risk_scenarios.py"
PORTFOLIO_RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_series_paper_portfolio.py"
GATES_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_regression_gates.py"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_local_snapshot_series_risk_scenarios.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_local_snapshot_series_risk_scenarios.v1.md"


def _frag(*parts):
    return "".join(parts)


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class RunLocalSnapshotSeriesRiskScenariosTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_every_required_end_to_end_scenario_is_exercised(self):
        payload = json.loads(_run_json().stdout)
        scenario_ids = {row["scenario_id"] for row in payload["scenario_reports"]}
        self.assertEqual(
            scenario_ids,
            {
                "baseline_valid_order_allowed",
                "duplicate_market_side_blocked",
                "total_exposure_breach_blocked",
                "asset_exposure_breach_blocked",
                "max_orders_per_snapshot_breach_blocked",
                "max_open_positions_breach_blocked",
                "mixed_allowed_and_blocked_orders",
            },
        )
        self.assertEqual(payload["scenario_suite_summary"]["scenario_count"], 7)

    def test_risk_limit_reason_counts_cover_all_limit_types(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(
            payload["scenario_suite_summary"]["risk_limit_reason_counts"],
            {
                "max_total_paper_exposure_exceeded": 3,
                "max_asset_paper_exposure_exceeded": 1,
                "max_orders_per_snapshot_exceeded": 2,
                "max_open_positions_exceeded": 1,
            },
        )

    def test_allowed_duplicate_and_risk_blocks_are_reported(self):
        payload = json.loads(_run_json().stdout)
        summary = payload["scenario_suite_summary"]
        self.assertEqual(summary["paper_orders_created"], 7)
        self.assertEqual(summary["duplicate_orders_blocked"], 2)
        self.assertEqual(summary["risk_limit_orders_blocked"], 6)
        self.assertEqual(summary["bad_entries"], 0)
        mixed = next(row for row in payload["scenario_reports"] if row["scenario_id"] == "mixed_allowed_and_blocked_orders")
        self.assertEqual(mixed["scenario_summary"]["paper_orders_created"], 1)
        self.assertEqual(mixed["scenario_summary"]["duplicate_orders_blocked"], 1)
        self.assertEqual(mixed["scenario_summary"]["risk_limit_orders_blocked"], 2)

    def test_realized_pnl_and_safety_flags_are_locked(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["scenario_suite_summary"]["realized_paper_pnl"], 100.0)
        self.assertTrue(payload["scenario_suite_summary"]["safety_flags_locked"])
        for key in (
            "offline_only",
            "paper_only",
        ):
            self.assertTrue(payload[key])
        for key in (
            "live_fetcher_implemented",
            "execution_allowed",
            "trading_allowed",
            "real_order_created",
            "wallet_used",
            "api_used",
            "network_used",
        ):
            self.assertFalse(payload[key])

    def test_existing_portfolio_command_still_works(self):
        payload = json.loads(subprocess.run([sys.executable, str(PORTFOLIO_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        self.assertEqual(payload["portfolio_series_summary"]["risk_limit_orders_blocked"], 1)
        self.assertTrue(payload["portfolio_series_summary"]["safety_flags_locked"])

    def test_lifecycle_regression_gates_still_pass(self):
        payload = json.loads(subprocess.run([sys.executable, str(GATES_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        self.assertEqual(payload["status"], "passed")
        self.assertTrue(payload["gates_summary"]["safety_flags_locked"])

    def test_no_runtime_or_network_behavior(self):
        source = RUNNER.read_text(encoding="utf-8").lower()
        forbidden = [
            _frag("re", "quests"),
            _frag("urllib", ".", "request"),
            "socket",
            _frag("dispatch", "er"),
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
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
