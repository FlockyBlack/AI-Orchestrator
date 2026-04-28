import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _path_normalization import normalize_repo_root_paths


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_paper_portfolio_state.py"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_local_snapshot_paper_portfolio_state.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_local_snapshot_paper_portfolio_state.v1.md"
EXPECTED_STATE = ROOT / "pm_bot" / "paper" / "paper_portfolio_state_after_snapshot.v1.json"
PORTFOLIO_RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_series_paper_portfolio.py"
SCENARIO_RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_series_risk_scenarios.py"
GATES_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_regression_gates.py"


def _frag(*parts):
    return "".join(parts)


def _run_json(*args):
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class RunLocalSnapshotPaperPortfolioStateTests(unittest.TestCase):
    def test_default_json_output_matches_expected(self):
        self.assertEqual(
            normalize_repo_root_paths(json.loads(_run_json().stdout), ROOT),
            json.loads(EXPECTED_JSON.read_text(encoding="utf-8")),
        )

    def test_markdown_output_matches_expected(self):
        self.assertEqual(
            normalize_repo_root_paths(_run_markdown().stdout, ROOT),
            EXPECTED_MD.read_text(encoding="utf-8"),
        )

    def test_out_state_writes_expected_state_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_state = Path(temp_dir) / "state.json"
            payload = json.loads(_run_json("--out-state", str(out_state)).stdout)
            self.assertTrue(payload["run_summary"]["out_state_written"])
            self.assertEqual(json.loads(out_state.read_text(encoding="utf-8")), json.loads(EXPECTED_STATE.read_text(encoding="utf-8")))

    def test_rerunning_with_written_state_blocks_duplicate_orders(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first_state = Path(temp_dir) / "state_after_first.json"
            _run_json("--out-state", str(first_state))
            second = json.loads(_run_json("--state", str(first_state), "--snapshot", str(ROOT / "pm_bot" / "paper" / "local_snapshot_series_fixture.v1.json")).stdout)
            self.assertEqual(second["input_snapshot"]["snapshot_id"], "series_snapshot_003")
            self.assertEqual(second["run_summary"]["new_paper_orders_created"], 0)
            self.assertEqual(second["run_summary"]["duplicate_orders_blocked"], 0)
            self.assertEqual(second["run_summary"]["settled_positions_after_run"], 1)
            self.assertEqual(second["run_summary"]["realized_paper_pnl_after_run"], 72.41)

    def test_risk_limits_account_for_existing_state_exposure(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["input_state"]["summary"]["open_paper_notional"], 100.0)
        self.assertEqual(payload["run_summary"]["new_paper_orders_created"], 0)
        self.assertEqual(payload["run_summary"]["duplicate_orders_blocked"], 1)
        self.assertEqual(payload["run_summary"]["risk_limit_orders_blocked"], 1)
        self.assertEqual(
            payload["run_summary"]["risk_limit_reason_counts"],
            {
                "max_total_paper_exposure_exceeded": 1,
                "max_open_positions_exceeded": 1,
            },
        )

    def test_existing_portfolio_and_scenario_commands_still_work(self):
        portfolio = json.loads(subprocess.run([sys.executable, str(PORTFOLIO_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        scenarios = json.loads(subprocess.run([sys.executable, str(SCENARIO_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        self.assertTrue(portfolio["portfolio_series_summary"]["safety_flags_locked"])
        self.assertTrue(scenarios["scenario_suite_summary"]["safety_flags_locked"])

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
