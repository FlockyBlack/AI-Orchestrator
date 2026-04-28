import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_inbox_paper_portfolio.py"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_local_snapshot_inbox_paper_portfolio.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_local_snapshot_inbox_paper_portfolio.v1.md"
EXPECTED_LEDGER = ROOT / "pm_bot" / "paper" / "expected_local_snapshot_inbox_run_ledger.v1.json"
EXPECTED_STATE = ROOT / "pm_bot" / "paper" / "paper_portfolio_state_after_inbox.v1.json"
STATE_RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_paper_portfolio_state.py"
SCENARIO_RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_series_risk_scenarios.py"
GATES_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_regression_gates.py"


def _frag(*parts):
    return "".join(parts)


def _run_json(*args):
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown(*args):
    return subprocess.run([sys.executable, str(RUNNER), "--markdown", *args], cwd=ROOT, capture_output=True, text=True, check=True)


class RunLocalSnapshotInboxPaperPortfolioTests(unittest.TestCase):
    def test_default_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_is_deterministic(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_default_command_does_not_write_state_or_run_ledger(self):
        payload = json.loads(_run_json().stdout)
        self.assertIsNone(payload["run_summary"]["out_state_path"])
        self.assertFalse(payload["run_summary"]["out_state_written"])
        self.assertIsNone(payload["run_summary"]["out_run_ledger_path"])
        self.assertFalse(payload["run_summary"]["out_run_ledger_written"])

    def test_out_run_ledger_writes_expected_deterministic_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_ledger = Path(temp_dir) / "run_ledger.json"
            payload = json.loads(_run_json("--run-id", "fixture-run-001", "--out-run-ledger", str(out_ledger)).stdout)
            self.assertTrue(payload["run_summary"]["out_run_ledger_written"])
            self.assertEqual(payload["run_summary"]["out_run_ledger_path"], str(out_ledger))
            self.assertEqual(json.loads(out_ledger.read_text(encoding="utf-8")), json.loads(EXPECTED_LEDGER.read_text(encoding="utf-8")))

    def test_run_id_controls_deterministic_run_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_ledger = Path(temp_dir) / "run_ledger.json"
            _run_json("--run-id", "manual-run-abc", "--out-run-ledger", str(out_ledger))
            ledger = json.loads(out_ledger.read_text(encoding="utf-8"))
            self.assertEqual(ledger["run_id"], "manual-run-abc")

    def test_run_ledger_records_snapshots_state_summaries_and_safety(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_ledger = Path(temp_dir) / "run_ledger.json"
            _run_json("--run-id", "fixture-run-001", "--out-run-ledger", str(out_ledger))
            ledger = json.loads(out_ledger.read_text(encoding="utf-8"))
            self.assertEqual(len(ledger["snapshot_files_discovered"]), 3)
            self.assertEqual([row["snapshot_id"] for row in ledger["snapshots_skipped_already_processed"]], ["series_snapshot_001"])
            self.assertEqual([row["snapshot_id"] for row in ledger["snapshots_processed"]], ["series_snapshot_002", "series_snapshot_003"])
            self.assertTrue(all(len(row["sha256"]) == 64 for row in ledger["snapshot_files_discovered"]))
            self.assertEqual(ledger["before_state_summary"]["processed_snapshots"], 1)
            self.assertEqual(ledger["after_state_summary"]["processed_snapshots"], 3)
            self.assertTrue(ledger["offline_only"])
            self.assertTrue(ledger["paper_only"])
            self.assertFalse(ledger["live_fetcher_implemented"])
            self.assertFalse(ledger["api_used"])
            self.assertFalse(ledger["network_used"])

    def test_out_state_and_out_run_ledger_can_be_used_together(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_state = Path(temp_dir) / "state_after_inbox.json"
            out_ledger = Path(temp_dir) / "run_ledger.json"
            payload = json.loads(_run_json("--out-state", str(out_state), "--out-run-ledger", str(out_ledger)).stdout)
            self.assertTrue(payload["run_summary"]["out_state_written"])
            self.assertTrue(payload["run_summary"]["out_run_ledger_written"])
            ledger = json.loads(out_ledger.read_text(encoding="utf-8"))
            self.assertEqual(ledger["output_state_path"], str(out_state))

    def test_out_state_writes_expected_final_state_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_state = Path(temp_dir) / "state_after_inbox.json"
            payload = json.loads(_run_json("--out-state", str(out_state)).stdout)
            self.assertTrue(payload["run_summary"]["out_state_written"])
            self.assertEqual(json.loads(out_state.read_text(encoding="utf-8")), json.loads(EXPECTED_STATE.read_text(encoding="utf-8")))

    def test_rerunning_with_written_state_skips_already_processed_snapshots(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_state = Path(temp_dir) / "state_after_inbox.json"
            _run_json("--out-state", str(out_state))
            payload = json.loads(_run_json("--state", str(out_state)).stdout)
            self.assertEqual(payload["run_summary"]["snapshot_files_discovered"], 3)
            self.assertEqual(payload["run_summary"]["snapshots_skipped_already_processed"], 3)
            self.assertEqual(payload["run_summary"]["snapshots_processed"], 0)
            self.assertEqual(payload["run_summary"]["new_paper_orders_created"], 0)
            self.assertEqual(payload["run_summary"]["duplicate_orders_blocked"], 0)
            self.assertEqual(payload["run_summary"]["risk_limit_orders_blocked"], 0)
            self.assertEqual(payload["run_summary"]["settled_positions_after_run"], 1)
            self.assertEqual(payload["run_summary"]["realized_paper_pnl_after_run"], 72.41)

    def test_rerunning_with_written_state_produces_skip_ledger(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_state = Path(temp_dir) / "state_after_inbox.json"
            out_ledger = Path(temp_dir) / "rerun_ledger.json"
            _run_json("--out-state", str(out_state))
            _run_json("--state", str(out_state), "--run-id", "rerun-skip-001", "--out-run-ledger", str(out_ledger))
            ledger = json.loads(out_ledger.read_text(encoding="utf-8"))
            self.assertEqual(ledger["run_id"], "rerun-skip-001")
            self.assertEqual(len(ledger["snapshot_files_discovered"]), 3)
            self.assertEqual(len(ledger["snapshots_skipped_already_processed"]), 3)
            self.assertEqual(ledger["snapshots_processed"], [])
            self.assertEqual(ledger["realized_paper_pnl_delta"], 0.0)
            self.assertEqual(ledger["final_realized_paper_pnl"], 72.41)

    def test_duplicate_blocking_works_across_inbox_snapshots(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["snapshots_skipped_already_processed"][0]["snapshot_id"], "series_snapshot_001")
        self.assertEqual(payload["snapshot_reports"][0]["snapshot_id"], "series_snapshot_002")
        self.assertEqual(payload["snapshot_reports"][0]["duplicate_orders_blocked"], 1)
        self.assertEqual(
            sum(1 for row in payload["portfolio_events"] if row["event_type"] == "duplicate_paper_order_blocked"),
            1,
        )

    def test_risk_limits_account_for_carried_state_across_inbox_snapshots(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["input_state"]["summary"]["open_paper_notional"], 100.0)
        self.assertEqual(payload["snapshot_reports"][0]["risk_limit_orders_blocked"], 1)
        self.assertEqual(
            payload["run_summary"]["risk_limit_reason_counts"],
            {
                "max_total_paper_exposure_exceeded": 1,
                "max_open_positions_exceeded": 1,
            },
        )

    def test_existing_state_and_risk_commands_still_pass(self):
        state_payload = json.loads(subprocess.run([sys.executable, str(STATE_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        scenario_payload = json.loads(subprocess.run([sys.executable, str(SCENARIO_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        self.assertTrue(state_payload["run_summary"]["safety_flags_locked"])
        self.assertTrue(scenario_payload["scenario_suite_summary"]["safety_flags_locked"])

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
        self.assertLessEqual(imports, {"argparse", "hashlib", "importlib", "json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
