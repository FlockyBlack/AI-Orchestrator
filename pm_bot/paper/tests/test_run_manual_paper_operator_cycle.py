import ast
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_paper_operator_cycle.py"
SOURCE = ROOT / "pm_bot" / "paper" / "manual_snapshot_import_source"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_manual_paper_operator_cycle.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_manual_paper_operator_cycle.v1.md"
EXPECTED_THRESHOLD_JSON = ROOT / "pm_bot" / "paper" / "expected_manual_paper_operator_cycle_threshold_hit_review.v1.json"
EXPECTED_THRESHOLD_MD = ROOT / "pm_bot" / "paper" / "expected_manual_paper_operator_cycle_threshold_hit_review.v1.md"
EXPECTED_MANIFEST = ROOT / "pm_bot" / "paper" / "expected_manual_paper_operator_cycle_manifest.v1.json"
EXPECTED_STATE = ROOT / "pm_bot" / "paper" / "paper_portfolio_state_after_inbox.v1.json"
FIXTURE_WORKSPACE = ROOT / "pm_bot" / "paper" / "manual_paper_workspace"
IMPORT_RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_snapshot_workspace_import.py"
WORKSPACE_RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_paper_workspace.py"
SCENARIO_RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_series_risk_scenarios.py"
GATES_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_regression_gates.py"
THRESHOLD_REVIEW_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_threshold_hit_review_table.py"
THRESHOLD_POLICY_SCENARIOS_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_threshold_hit_policy_scenarios.py"
REFERENCE_CONTEXT = ROOT / "pm_bot" / "paper" / "threshold_hit_reference_context.v1.json"
DECISION_POLICY = ROOT / "pm_bot" / "paper" / "threshold_hit_decision_policy.v1.json"


def _frag(*parts):
    return "".join(parts)


def _run_json(*args, check=True):
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, capture_output=True, text=True, check=check)


def _run_markdown(*args):
    return subprocess.run([sys.executable, str(RUNNER), "--markdown", *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _threshold_review_args():
    return (
        "--include-threshold-hit-review",
        "--threshold-reference-context",
        str(REFERENCE_CONTEXT),
        "--threshold-decision-policy",
        str(DECISION_POLICY),
    )


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


class RunManualPaperOperatorCycleTests(unittest.TestCase):
    def test_default_command_is_read_only_and_deterministic(self):
        before = _fixture_file_snapshot()
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload, json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))
        self.assertFalse(payload["summary"]["inbox_files_written"])
        self.assertFalse(payload["summary"]["manifest_written"])
        self.assertFalse(payload["summary"]["run_artifacts_written"])
        self.assertFalse(payload["summary"]["state_committed"])
        self.assertTrue(payload["workspace_phase"]["imported_snapshots_previewed_but_not_added_to_inbox"])
        self.assertFalse((FIXTURE_WORKSPACE / "inbox" / "004_series_snapshot_004.json").exists())
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_markdown_stdout_is_deterministic(self):
        before = _fixture_file_snapshot()
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_threshold_hit_review_json_stdout_is_deterministic(self):
        before = _fixture_file_snapshot()
        first = _run_json(*_threshold_review_args()).stdout
        second = _run_json(*_threshold_review_args()).stdout
        self.assertEqual(first, second)
        payload = json.loads(first)
        self.assertEqual(payload, json.loads(EXPECTED_THRESHOLD_JSON.read_text(encoding="utf-8")))
        self.assertTrue(payload["summary"]["threshold_hit_review_included"])
        self.assertEqual(payload["summary"]["threshold_hit_candidates"], 3)
        self.assertEqual(payload["summary"]["threshold_hit_watchlist_count"], 2)
        self.assertEqual(payload["summary"]["threshold_hit_policy_blocked_count"], 1)
        self.assertEqual(payload["summary"]["threshold_hit_paper_candidate_count"], 0)
        self.assertEqual(payload["summary"]["threshold_hit_paper_orders_created"], 0)
        self.assertEqual(payload["summary"]["threshold_hit_artifact_paths"], {})
        self.assertEqual(payload["summary"]["new_paper_orders_created"], 0)
        self.assertFalse(payload["summary"]["state_committed"])
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_threshold_hit_review_markdown_stdout_is_deterministic(self):
        before = _fixture_file_snapshot()
        first = _run_markdown(*_threshold_review_args()).stdout
        second = _run_markdown(*_threshold_review_args()).stdout
        self.assertEqual(first, second)
        self.assertEqual(first, EXPECTED_THRESHOLD_MD.read_text(encoding="utf-8"))
        self.assertIn("- threshold_hit_review_included: true", first)
        self.assertIn("- threshold_hit_paper_orders_created: 0", first)
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_write_inbox_writes_imported_snapshot_files_only_in_temp_workspace_copy(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            original_state = (workspace / "state" / "current_state.json").read_bytes()
            payload = json.loads(_run_json("--workspace", str(workspace), "--write-inbox").stdout)
            inbox = workspace / "inbox"
            self.assertEqual(payload["summary"]["imported_snapshot_count"], 2)
            self.assertTrue(payload["summary"]["inbox_files_written"])
            self.assertFalse(payload["summary"]["run_artifacts_written"])
            self.assertFalse(payload["summary"]["state_committed"])
            self.assertEqual(
                sorted(path.name for path in inbox.iterdir() if path.is_file()),
                [
                    "001_series_snapshot_001.json",
                    "002_series_snapshot_002.json",
                    "003_series_snapshot_003.json",
                    "004_series_snapshot_004.json",
                    "005_series_snapshot_005.json",
                ],
            )
            self.assertEqual(json.loads((inbox / "004_series_snapshot_004.json").read_text(encoding="utf-8")), json.loads((SOURCE / "001_series_snapshot_004.json").read_text(encoding="utf-8")))
            self.assertEqual(json.loads((inbox / "005_series_snapshot_005.json").read_text(encoding="utf-8")), json.loads((SOURCE / "002_series_snapshot_005.json").read_text(encoding="utf-8")))
            self.assertEqual((workspace / "state" / "current_state.json").read_bytes(), original_state)
            self.assertEqual(list((workspace / "runs").iterdir()), [])
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_out_manifest_writes_deterministic_import_manifest(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            out_manifest = Path(temp_dir) / "operator_cycle_import_manifest.json"
            payload = json.loads(_run_json("--out-manifest", str(out_manifest)).stdout)
            self.assertTrue(payload["summary"]["manifest_written"])
            self.assertTrue(payload["import_phase"]["manifest_written"])
            self.assertEqual(payload["import_phase"]["manifest_path"], str(out_manifest))
            self.assertEqual(json.loads(out_manifest.read_text(encoding="utf-8")), json.loads(EXPECTED_MANIFEST.read_text(encoding="utf-8")))
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_write_run_writes_run_artifacts_without_committing_state(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            original_state = (workspace / "state" / "current_state.json").read_bytes()
            payload = json.loads(_run_json("--workspace", str(workspace), "--run-id", "operator-cycle-write-run", "--write-run").stdout)
            run_dir = workspace / "runs" / "operator-cycle-write-run"
            self.assertTrue(payload["summary"]["run_artifacts_written"])
            self.assertFalse(payload["summary"]["state_committed"])
            self.assertFalse(payload["summary"]["inbox_files_written"])
            self.assertEqual(sorted(path.name for path in run_dir.iterdir()), ["run_ledger.json", "run_summary.md", "state_after.json", "state_before.json"])
            self.assertEqual(json.loads((run_dir / "state_after.json").read_text(encoding="utf-8")), json.loads(EXPECTED_STATE.read_text(encoding="utf-8")))
            self.assertEqual((workspace / "state" / "current_state.json").read_bytes(), original_state)
            self.assertFalse((workspace / "state" / "current_state.previous.json").exists())
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_threshold_hit_review_write_run_writes_artifacts_without_committing_state(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            original_state = (workspace / "state" / "current_state.json").read_bytes()
            payload = json.loads(_run_json(
                "--workspace",
                str(workspace),
                "--run-id",
                "operator-cycle-threshold-write-run",
                "--write-run",
                *_threshold_review_args(),
            ).stdout)
            run_dir = workspace / "runs" / "operator-cycle-threshold-write-run"
            json_artifact = run_dir / "threshold_hit_review.json"
            markdown_artifact = run_dir / "threshold_hit_review.md"
            self.assertTrue(payload["summary"]["run_artifacts_written"])
            self.assertFalse(payload["summary"]["state_committed"])
            self.assertEqual(
                sorted(path.name for path in run_dir.iterdir()),
                [
                    "run_ledger.json",
                    "run_summary.md",
                    "state_after.json",
                    "state_before.json",
                    "threshold_hit_review.json",
                    "threshold_hit_review.md",
                ],
            )
            self.assertEqual(
                payload["summary"]["threshold_hit_artifact_paths"],
                {"json": str(json_artifact), "markdown": str(markdown_artifact)},
            )
            threshold_payload = json.loads(json_artifact.read_text(encoding="utf-8"))
            self.assertEqual(threshold_payload["summary"]["threshold_hit_candidates"], 3)
            self.assertEqual(threshold_payload["summary"]["paper_orders_created"], 0)
            self.assertIn("# Crypto Threshold-Hit Review Table", markdown_artifact.read_text(encoding="utf-8"))
            self.assertEqual((workspace / "state" / "current_state.json").read_bytes(), original_state)
            self.assertFalse((workspace / "state" / "current_state.previous.json").exists())
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_commit_state_writes_run_artifacts_and_promotes_current_state(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            payload = json.loads(_run_json("--workspace", str(workspace), "--run-id", "operator-cycle-commit", "--write-inbox", "--commit-state").stdout)
            run_dir = workspace / "runs" / "operator-cycle-commit"
            self.assertTrue(payload["summary"]["inbox_files_written"])
            self.assertTrue(payload["summary"]["run_artifacts_written"])
            self.assertTrue(payload["summary"]["state_committed"])
            self.assertTrue(payload["write_controls"]["commit_state_implies_write_run"])
            self.assertTrue((workspace / "state" / "current_state.previous.json").exists())
            self.assertEqual(json.loads((workspace / "state" / "current_state.json").read_text(encoding="utf-8")), json.loads((run_dir / "state_after.json").read_text(encoding="utf-8")))
            self.assertEqual(payload["workspace_phase"]["current_state_after_command"]["processed_snapshots"], 5)
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_threshold_hit_review_does_not_mutate_state_or_create_paper_orders(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            original_state = (workspace / "state" / "current_state.json").read_bytes()
            payload = json.loads(_run_json("--workspace", str(workspace), *_threshold_review_args()).stdout)
            self.assertFalse(payload["summary"]["run_artifacts_written"])
            self.assertFalse(payload["summary"]["state_committed"])
            self.assertEqual(payload["summary"]["new_paper_orders_created"], 0)
            self.assertEqual(payload["summary"]["threshold_hit_paper_orders_created"], 0)
            self.assertEqual(payload["summary"]["threshold_hit_artifact_paths"], {})
            self.assertEqual((workspace / "state" / "current_state.json").read_bytes(), original_state)
            self.assertEqual(list((workspace / "runs").iterdir()), [])
            self.assertNotIn("paper_orders", payload)
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_threshold_hit_review_commit_state_matches_normal_workspace_state(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            normal_workspace = Path(temp_dir) / "normal"
            threshold_workspace = Path(temp_dir) / "threshold"
            shutil.copytree(FIXTURE_WORKSPACE, normal_workspace)
            shutil.copytree(FIXTURE_WORKSPACE, threshold_workspace)
            normal_payload = json.loads(_run_json(
                "--workspace",
                str(normal_workspace),
                "--run-id",
                "operator-cycle-normal-commit",
                "--write-inbox",
                "--commit-state",
            ).stdout)
            threshold_payload = json.loads(_run_json(
                "--workspace",
                str(threshold_workspace),
                "--run-id",
                "operator-cycle-threshold-commit",
                "--write-inbox",
                "--commit-state",
                *_threshold_review_args(),
            ).stdout)
            threshold_run_dir = threshold_workspace / "runs" / "operator-cycle-threshold-commit"
            self.assertTrue(threshold_payload["summary"]["state_committed"])
            self.assertEqual(threshold_payload["summary"]["threshold_hit_paper_orders_created"], 0)
            self.assertEqual(
                json.loads((normal_workspace / "state" / "current_state.json").read_text(encoding="utf-8")),
                json.loads((threshold_workspace / "state" / "current_state.json").read_text(encoding="utf-8")),
            )
            self.assertEqual(
                json.loads((threshold_workspace / "state" / "current_state.json").read_text(encoding="utf-8")),
                json.loads((threshold_run_dir / "state_after.json").read_text(encoding="utf-8")),
            )
            self.assertEqual(
                normal_payload["workspace_phase"]["current_state_after_command"],
                threshold_payload["workspace_phase"]["current_state_after_command"],
            )
            self.assertNotIn("threshold_hit", (threshold_workspace / "state" / "current_state.json").read_text(encoding="utf-8"))
            self.assertTrue((threshold_run_dir / "threshold_hit_review.json").exists())
            self.assertTrue((threshold_run_dir / "threshold_hit_review.md").exists())
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_imported_snapshots_are_included_only_when_write_inbox_is_used(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            preview_workspace = Path(temp_dir) / "preview"
            write_workspace = Path(temp_dir) / "write"
            shutil.copytree(FIXTURE_WORKSPACE, preview_workspace)
            shutil.copytree(FIXTURE_WORKSPACE, write_workspace)
            preview_payload = json.loads(_run_json("--workspace", str(preview_workspace)).stdout)
            write_payload = json.loads(_run_json("--workspace", str(write_workspace), "--write-inbox").stdout)
            self.assertFalse(preview_payload["workspace_phase"]["workspace_phase_includes_imported_snapshots"])
            self.assertTrue(preview_payload["workspace_phase"]["imported_snapshots_previewed_but_not_added_to_inbox"])
            self.assertEqual(preview_payload["summary"]["workspace_snapshots_discovered"], 3)
            self.assertTrue(write_payload["workspace_phase"]["workspace_phase_includes_imported_snapshots"])
            self.assertFalse(write_payload["workspace_phase"]["imported_snapshots_previewed_but_not_added_to_inbox"])
            self.assertEqual(write_payload["summary"]["workspace_snapshots_discovered"], 5)
            self.assertEqual(write_payload["summary"]["workspace_snapshots_processed"], 4)
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_bad_source_files_are_quarantined_without_blocking_valid_imports(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["import_phase"]["importable_snapshots"], 2)
        self.assertEqual(payload["import_phase"]["skipped_or_quarantined_inputs"], 5)
        self.assertEqual(payload["import_phase"]["reason_counts"], {
            "already_present_in_workspace_inbox": 1,
            "duplicate_snapshot_id_in_source_batch": 1,
            "ignored_non_json_file": 1,
            "malformed_json": 1,
            "unsupported_snapshot_shape": 1,
        })
        by_file = {row["file_name"]: row for row in payload["import_phase"]["skipped_quarantined_records"]}
        self.assertEqual(by_file["005_malformed.json"]["status"], "quarantined")
        self.assertEqual(by_file["006_unsupported.json"]["reason_code"], "unsupported_snapshot_shape")

    def test_existing_run_id_collision_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            _run_json("--workspace", str(workspace), "--run-id", "operator-cycle-write-run", "--write-run")
            result = _run_json("--workspace", str(workspace), "--run-id", "operator-cycle-write-run", "--write-run", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("Run directory already exists", result.stderr)

    def test_canonical_fixture_workspace_has_not_been_mutated(self):
        self.assertEqual(
            sorted(path.name for path in (FIXTURE_WORKSPACE / "inbox").iterdir() if path.is_file()),
            ["001_series_snapshot_001.json", "002_series_snapshot_002.json", "003_series_snapshot_003.json"],
        )
        self.assertFalse((FIXTURE_WORKSPACE / "inbox" / "004_series_snapshot_004.json").exists())
        self.assertFalse((FIXTURE_WORKSPACE / "inbox" / "005_series_snapshot_005.json").exists())
        self.assertFalse((FIXTURE_WORKSPACE / "state" / "current_state.previous.json").exists())
        self.assertEqual([path.name for path in (FIXTURE_WORKSPACE / "runs").iterdir() if path.is_file()], [])

    def test_existing_manual_commands_and_lifecycle_gates_still_pass(self):
        import_payload = json.loads(subprocess.run([sys.executable, str(IMPORT_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        workspace_payload = json.loads(subprocess.run([sys.executable, str(WORKSPACE_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        subprocess.run([sys.executable, str(WORKSPACE_RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)
        threshold_review = subprocess.run(
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
        threshold_policy = json.loads(subprocess.run(
            [sys.executable, str(THRESHOLD_POLICY_SCENARIOS_RUNNER)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout)
        scenario_payload = json.loads(subprocess.run([sys.executable, str(SCENARIO_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        gates_payload = json.loads(subprocess.run([sys.executable, str(GATES_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        self.assertTrue(import_payload["safety_flags"]["offline_only"])
        self.assertTrue(workspace_payload["offline_only"])
        self.assertIn("- Threshold-hit candidates: 3", threshold_review.stdout)
        self.assertEqual(threshold_policy["summary"]["paper_orders_created"], 0)
        self.assertTrue(threshold_policy["summary"]["all_expected_decisions_passed"])
        self.assertTrue(scenario_payload["scenario_suite_summary"]["safety_flags_locked"])
        self.assertEqual(gates_payload["status"], "passed")

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
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
