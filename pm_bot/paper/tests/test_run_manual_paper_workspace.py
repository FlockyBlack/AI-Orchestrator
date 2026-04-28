import ast
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _path_normalization import normalize_repo_root_paths


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_paper_workspace.py"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_manual_paper_workspace.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_manual_paper_workspace_summary.v1.md"
EXPECTED_STATE = ROOT / "pm_bot" / "paper" / "paper_portfolio_state_after_inbox.v1.json"
FIXTURE_WORKSPACE = ROOT / "pm_bot" / "paper" / "manual_paper_workspace"
BUNDLE_RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_paper_inbox_bundle.py"
INBOX_RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_inbox_paper_portfolio.py"
SCENARIO_RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_series_risk_scenarios.py"
GATES_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_regression_gates.py"


def _frag(*parts):
    return "".join(parts)


def _run_json(*args, check=True):
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, capture_output=True, text=True, check=check)


def _run_markdown(*args):
    return subprocess.run([sys.executable, str(RUNNER), "--markdown", *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _make_workspace(temp_dir):
    workspace = Path(temp_dir) / "workspace"
    shutil.copytree(FIXTURE_WORKSPACE, workspace)
    runs = workspace / "runs"
    if runs.exists():
        shutil.rmtree(runs)
    runs.mkdir(parents=True)
    return workspace


def _fixture_file_snapshot():
    return {
        path.relative_to(FIXTURE_WORKSPACE).as_posix(): path.read_bytes()
        for path in sorted(FIXTURE_WORKSPACE.rglob("*"))
        if path.is_file()
    }


class RunManualPaperWorkspaceTests(unittest.TestCase):
    def test_default_command_is_read_only_and_deterministic(self):
        before = _fixture_file_snapshot()
        payload = json.loads(_run_json().stdout)
        self.assertEqual(
            normalize_repo_root_paths(payload, ROOT),
            json.loads(EXPECTED_JSON.read_text(encoding="utf-8")),
        )
        self.assertFalse(payload["run_artifacts_written"])
        self.assertFalse(payload["state_committed"])
        self.assertIsNone(payload["run_directory_path"])
        self.assertEqual(payload["output_files"], [])
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_markdown_stdout_is_deterministic(self):
        before = _fixture_file_snapshot()
        self.assertEqual(
            normalize_repo_root_paths(_run_markdown().stdout, ROOT),
            EXPECTED_MD.read_text(encoding="utf-8"),
        )
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_canonical_fixture_workspace_has_no_mutable_run_artifacts(self):
        self.assertFalse((FIXTURE_WORKSPACE / "state" / "current_state.previous.json").exists())
        run_files = [
            path.relative_to(FIXTURE_WORKSPACE).as_posix()
            for path in (FIXTURE_WORKSPACE / "runs").rglob("*")
            if path.is_file() and path.name != ".gitkeep"
        ]
        self.assertEqual(run_files, [])

    def test_write_run_writes_expected_run_folder_files(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            payload = json.loads(_run_json("--workspace", str(workspace), "--run-id", "fixture-run-001", "--write-run").stdout)
            run_dir = workspace / "runs" / "fixture-run-001"
            self.assertTrue(payload["run_artifacts_written"])
            self.assertFalse(payload["state_committed"])
            self.assertEqual(sorted(path.name for path in run_dir.iterdir()), ["run_ledger.json", "run_summary.md", "state_after.json", "state_before.json"])
            self.assertEqual(json.loads((run_dir / "state_after.json").read_text(encoding="utf-8")), json.loads(EXPECTED_STATE.read_text(encoding="utf-8")))
            ledger = json.loads((run_dir / "run_ledger.json").read_text(encoding="utf-8"))
            summary = (run_dir / "run_summary.md").read_text(encoding="utf-8")
            self.assertEqual(ledger["quarantine_reason_counts"], {"already_processed_snapshot": 1})
            self.assertIn("## Quarantine", summary)
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_commit_state_writes_run_folder_and_updates_current_state(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            payload = json.loads(_run_json("--workspace", str(workspace), "--run-id", "fixture-run-002", "--commit-state").stdout)
            run_dir = workspace / "runs" / "fixture-run-002"
            self.assertTrue(payload["run_artifacts_written"])
            self.assertTrue(payload["state_committed"])
            self.assertTrue((workspace / "state" / "current_state.previous.json").exists())
            self.assertEqual(json.loads((workspace / "state" / "current_state.json").read_text(encoding="utf-8")), json.loads((run_dir / "state_after.json").read_text(encoding="utf-8")))
            ledger = json.loads((run_dir / "run_ledger.json").read_text(encoding="utf-8"))
            self.assertEqual(ledger["quarantine_count"], 1)
            self.assertEqual(ledger["quarantine_records"][0]["reason_code"], "already_processed_snapshot")
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_bad_local_inputs_are_quarantined_without_blocking_valid_snapshots(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            inbox = workspace / "inbox"
            (inbox / "004_duplicate_series_snapshot_002.json").write_text(
                (inbox / "002_series_snapshot_002.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (inbox / "005_malformed.json").write_text("{not json", encoding="utf-8")
            (inbox / "006_unsupported.json").write_text(json.dumps({"snapshot_id": "unsupported_shape"}), encoding="utf-8")
            (inbox / "007_notes.txt").write_text("operator note", encoding="utf-8")
            (inbox / "008_directory.json").mkdir()

            payload = json.loads(_run_json("--workspace", str(workspace)).stdout)
            self.assertFalse(payload["run_artifacts_written"])
            self.assertFalse(payload["state_committed"])
            self.assertEqual(payload["input_files_discovered"], 8)
            self.assertEqual(payload["valid_snapshot_files_discovered"], 3)
            self.assertEqual(payload["snapshots_processed"], 2)
            self.assertEqual(payload["snapshots_skipped_already_processed"], 1)
            self.assertEqual(payload["quarantine_reason_counts"], {
                "already_processed_snapshot": 1,
                "duplicate_snapshot_id_in_inbox": 1,
                "ignored_non_json_file": 1,
                "malformed_json": 1,
                "unreadable_input": 1,
                "unsupported_snapshot_shape": 1,
            })
            self.assertEqual(payload["current_state_after_command"]["processed_snapshots"], 1)
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_write_run_and_commit_preserve_quarantine_records_for_bad_inputs(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            inbox = workspace / "inbox"
            (inbox / "004_duplicate_series_snapshot_002.json").write_text(
                (inbox / "002_series_snapshot_002.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (inbox / "005_malformed.json").write_text("{not json", encoding="utf-8")
            (inbox / "006_unsupported.json").write_text(json.dumps({"snapshots": []}), encoding="utf-8")
            (inbox / "007_notes.txt").write_text("operator note", encoding="utf-8")

            write_payload = json.loads(_run_json("--workspace", str(workspace), "--run-id", "bad-inputs-write", "--write-run").stdout)
            write_run = workspace / "runs" / "bad-inputs-write"
            write_ledger = json.loads((write_run / "run_ledger.json").read_text(encoding="utf-8"))
            write_summary = (write_run / "run_summary.md").read_text(encoding="utf-8")
            self.assertEqual(write_payload["snapshots_processed"], 2)
            self.assertEqual(write_ledger["quarantine_count"], 5)
            self.assertIn("malformed_json", write_summary)
            self.assertIn("duplicate_snapshot_id_in_inbox", write_summary)

            commit_payload = json.loads(_run_json("--workspace", str(workspace), "--run-id", "bad-inputs-commit", "--commit-state").stdout)
            commit_run = workspace / "runs" / "bad-inputs-commit"
            commit_ledger = json.loads((commit_run / "run_ledger.json").read_text(encoding="utf-8"))
            self.assertTrue(commit_payload["state_committed"])
            self.assertEqual(commit_payload["snapshots_processed"], 2)
            self.assertEqual(commit_ledger["quarantine_reason_counts"], write_ledger["quarantine_reason_counts"])
            self.assertEqual(json.loads((workspace / "state" / "current_state.json").read_text(encoding="utf-8")), json.loads((commit_run / "state_after.json").read_text(encoding="utf-8")))
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_existing_run_id_collision_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            _run_json("--workspace", str(workspace), "--run-id", "fixture-run-001", "--write-run")
            result = _run_json("--workspace", str(workspace), "--run-id", "fixture-run-001", "--write-run", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("Run directory already exists", result.stderr)

    def test_allow_identical_rerun_only_accepts_matching_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            _run_json("--workspace", str(workspace), "--run-id", "fixture-run-001", "--write-run")
            payload = json.loads(_run_json("--workspace", str(workspace), "--run-id", "fixture-run-001", "--write-run", "--allow-identical-rerun").stdout)
            self.assertTrue(payload["run_artifacts_written"])
            (workspace / "runs" / "fixture-run-001" / "run_summary.md").write_text("changed\n", encoding="utf-8")
            result = _run_json("--workspace", str(workspace), "--run-id", "fixture-run-001", "--write-run", "--allow-identical-rerun", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("different content", result.stderr)

    def test_rerun_after_commit_skips_already_processed_snapshots(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            _run_json("--workspace", str(workspace), "--run-id", "fixture-run-002", "--commit-state")
            payload = json.loads(_run_json("--workspace", str(workspace), "--run-id", "post-commit-preview").stdout)
            self.assertEqual(payload["snapshots_processed"], 0)
            self.assertEqual(payload["snapshots_skipped_already_processed"], 3)
            self.assertEqual(payload["realized_paper_pnl_delta"], 0.0)
            self.assertEqual(payload["final_realized_paper_pnl"], 72.41)

    def test_state_before_and_state_after_are_preserved_in_run_folder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            _run_json("--workspace", str(workspace), "--run-id", "fixture-run-001", "--write-run")
            run_dir = workspace / "runs" / "fixture-run-001"
            before = json.loads((run_dir / "state_before.json").read_text(encoding="utf-8"))
            after = json.loads((run_dir / "state_after.json").read_text(encoding="utf-8"))
            self.assertEqual(before["processed_snapshot_ids"], ["series_snapshot_001"])
            self.assertEqual(after["processed_snapshot_ids"], ["series_snapshot_001", "series_snapshot_002", "series_snapshot_003"])

    def test_existing_bundle_inbox_risk_and_lifecycle_commands_still_pass(self):
        bundle_payload = json.loads(subprocess.run([sys.executable, str(BUNDLE_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        inbox_payload = json.loads(subprocess.run([sys.executable, str(INBOX_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        scenario_payload = json.loads(subprocess.run([sys.executable, str(SCENARIO_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        gates_payload = json.loads(subprocess.run([sys.executable, str(GATES_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        self.assertTrue(bundle_payload["offline_only"])
        self.assertTrue(inbox_payload["run_summary"]["safety_flags_locked"])
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
        self.assertLessEqual(imports, {"argparse", "hashlib", "importlib", "json", "shutil", "sys", "tempfile", "pathlib"})


if __name__ == "__main__":
    unittest.main()
