import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_paper_inbox_bundle.py"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_manual_paper_inbox_bundle.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_manual_paper_inbox_bundle_summary.v1.md"
EXPECTED_STATE = ROOT / "pm_bot" / "paper" / "paper_portfolio_state_after_inbox.v1.json"
EXPECTED_LEDGER = ROOT / "pm_bot" / "paper" / "expected_local_snapshot_inbox_run_ledger.v1.json"
INBOX_RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_inbox_paper_portfolio.py"
STATE_RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_paper_portfolio_state.py"
SCENARIO_RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_series_risk_scenarios.py"
GATES_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_regression_gates.py"


def _frag(*parts):
    return "".join(parts)


def _run_json(*args):
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown(*args):
    return subprocess.run([sys.executable, str(RUNNER), "--markdown", *args], cwd=ROOT, capture_output=True, text=True, check=True)


class RunManualPaperInboxBundleTests(unittest.TestCase):
    def test_default_command_is_read_only_and_deterministic(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload, json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))
        self.assertFalse(payload["bundle_written"])
        self.assertIsNone(payload["output_directory"])
        self.assertEqual(payload["output_files"], [])
        self.assertFalse(payload["inbox_report_summary"]["out_state_written"])
        self.assertFalse(payload["inbox_report_summary"]["out_run_ledger_written"])

    def test_markdown_stdout_is_deterministic(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_out_dir_writes_exactly_expected_three_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "bundle"
            payload = json.loads(_run_json("--run-id", "fixture-run-001", "--out-dir", str(out_dir)).stdout)
            self.assertTrue(payload["bundle_written"])
            self.assertEqual(sorted(path.name for path in out_dir.iterdir()), ["run_ledger.json", "run_summary.md", "state_after.json"])

    def test_state_after_matches_expected_final_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "bundle"
            _run_json("--run-id", "fixture-run-001", "--out-dir", str(out_dir))
            self.assertEqual(
                json.loads((out_dir / "state_after.json").read_text(encoding="utf-8")),
                json.loads(EXPECTED_STATE.read_text(encoding="utf-8")),
            )

    def test_run_ledger_matches_expected_shape_and_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "bundle"
            _run_json("--run-id", "fixture-run-001", "--out-dir", str(out_dir))
            ledger = json.loads((out_dir / "run_ledger.json").read_text(encoding="utf-8"))
            expected = json.loads(EXPECTED_LEDGER.read_text(encoding="utf-8"))
            expected["output_state_path"] = str(out_dir / "state_after.json")
            self.assertEqual(ledger, expected)

    def test_run_summary_md_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "bundle"
            _run_json("--run-id", "fixture-run-001", "--out-dir", str(out_dir))
            self.assertEqual((out_dir / "run_summary.md").read_text(encoding="utf-8"), _run_markdown("--run-id", "fixture-run-001", "--out-dir", str(out_dir)).stdout)

    def test_run_id_controls_artifact_contents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "bundle"
            payload = json.loads(_run_json("--run-id", "manual-run-xyz", "--out-dir", str(out_dir)).stdout)
            ledger = json.loads((out_dir / "run_ledger.json").read_text(encoding="utf-8"))
            summary = (out_dir / "run_summary.md").read_text(encoding="utf-8")
            self.assertEqual(payload["run_id"], "manual-run-xyz")
            self.assertEqual(ledger["run_id"], "manual-run-xyz")
            self.assertIn("- Run ID: manual-run-xyz", summary)

    def test_existing_inbox_state_risk_and_lifecycle_commands_still_pass(self):
        inbox_payload = json.loads(subprocess.run([sys.executable, str(INBOX_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        state_payload = json.loads(subprocess.run([sys.executable, str(STATE_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        scenario_payload = json.loads(subprocess.run([sys.executable, str(SCENARIO_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        gates_payload = json.loads(subprocess.run([sys.executable, str(GATES_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        self.assertTrue(inbox_payload["run_summary"]["safety_flags_locked"])
        self.assertTrue(state_payload["run_summary"]["safety_flags_locked"])
        self.assertTrue(scenario_payload["scenario_suite_summary"]["safety_flags_locked"])
        self.assertEqual(gates_payload["status"], "passed")

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["offline_only"])
        self.assertTrue(payload["paper_only"])
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
