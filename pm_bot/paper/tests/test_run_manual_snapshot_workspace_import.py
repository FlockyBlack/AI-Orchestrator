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
RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_snapshot_workspace_import.py"
SOURCE = ROOT / "pm_bot" / "paper" / "manual_snapshot_import_source"
POLYMARKET_FIXTURE = SOURCE / "008_polymarket_markets_active_minimized.fixture.json"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_manual_snapshot_workspace_import.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_manual_snapshot_workspace_import.v1.md"
EXPECTED_MANIFEST = ROOT / "pm_bot" / "paper" / "expected_manual_snapshot_import_manifest.v1.json"
FIXTURE_WORKSPACE = ROOT / "pm_bot" / "paper" / "manual_paper_workspace"
MANUAL_WORKSPACE_RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_paper_workspace.py"
MANUAL_BUNDLE_RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_paper_inbox_bundle.py"
SCENARIO_RUNNER = ROOT / "pm_bot" / "paper" / "run_local_snapshot_series_risk_scenarios.py"
GATES_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_regression_gates.py"


def _frag(*parts):
    return "".join(parts)


def _run_json(*args, check=True):
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, capture_output=True, text=True, check=check)


def _run_markdown(*args):
    return subprocess.run([sys.executable, str(RUNNER), "--markdown", *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _fixture_file_snapshot():
    return {
        path.relative_to(FIXTURE_WORKSPACE).as_posix(): path.read_bytes()
        for path in sorted(FIXTURE_WORKSPACE.rglob("*"))
        if path.is_file()
    }


def _make_workspace(temp_dir):
    workspace = Path(temp_dir) / "workspace"
    shutil.copytree(FIXTURE_WORKSPACE, workspace)
    return workspace


class RunManualSnapshotWorkspaceImportTests(unittest.TestCase):
    def test_default_command_is_read_only_and_deterministic(self):
        before = _fixture_file_snapshot()
        payload = json.loads(_run_json().stdout)
        self.assertEqual(
            normalize_repo_root_paths(payload, ROOT),
            json.loads(EXPECTED_JSON.read_text(encoding="utf-8")),
        )
        self.assertFalse(payload["write_inbox"])
        self.assertFalse(payload["manifest_written"])
        self.assertEqual(payload["summary"]["discovered_inputs"], 7)
        self.assertEqual(payload["summary"]["importable_snapshots"], 2)
        self.assertEqual(payload["summary"]["imported_snapshots"], 0)
        self.assertEqual(payload["output_inbox_files"], [])
        self.assertFalse((FIXTURE_WORKSPACE / "inbox" / "004_series_snapshot_004.json").exists())
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_markdown_stdout_is_deterministic(self):
        before = _fixture_file_snapshot()
        self.assertEqual(
            normalize_repo_root_paths(_run_markdown().stdout, ROOT),
            EXPECTED_MD.read_text(encoding="utf-8"),
        )
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_out_manifest_writes_expected_manifest_json(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            out_manifest = Path(temp_dir) / "import_manifest.json"
            payload = json.loads(_run_json("--out-manifest", str(out_manifest)).stdout)
            self.assertTrue(payload["manifest_written"])
            self.assertEqual(payload["manifest_path"], str(out_manifest))
            self.assertEqual(
                normalize_repo_root_paths(json.loads(out_manifest.read_text(encoding="utf-8")), ROOT),
                json.loads(EXPECTED_MANIFEST.read_text(encoding="utf-8")),
            )
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_write_inbox_writes_expected_canonical_snapshot_files_in_temp_workspace_copy(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            payload = json.loads(_run_json("--workspace", str(workspace), "--write-inbox").stdout)
            inbox = workspace / "inbox"
            self.assertEqual(payload["summary"]["imported_snapshots"], 2)
            self.assertEqual(
                [row["file_name"] for row in payload["output_inbox_files"]],
                ["004_series_snapshot_004.json", "005_series_snapshot_005.json"],
            )
            self.assertEqual(json.loads((inbox / "004_series_snapshot_004.json").read_text(encoding="utf-8")), json.loads((SOURCE / "001_series_snapshot_004.json").read_text(encoding="utf-8")))
            self.assertEqual(json.loads((inbox / "005_series_snapshot_005.json").read_text(encoding="utf-8")), json.loads((SOURCE / "002_series_snapshot_005.json").read_text(encoding="utf-8")))

            rerun = json.loads(_run_json("--workspace", str(workspace), "--write-inbox").stdout)
            self.assertEqual(rerun["summary"]["importable_snapshots"], 0)
            self.assertEqual(rerun["summary"]["imported_snapshots"], 0)
            self.assertEqual(rerun["output_inbox_files"], [])
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_required_input_classifications_are_reported(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["summary"]["skipped_or_quarantined_inputs"], 5)
        self.assertEqual(payload["reason_counts"], {
            "already_present_in_workspace_inbox": 1,
            "duplicate_snapshot_id_in_source_batch": 1,
            "ignored_non_json_file": 1,
            "malformed_json": 1,
            "unsupported_snapshot_shape": 1,
        })
        by_file = {row["file_name"]: row for row in payload["skipped_quarantined_records"]}
        self.assertEqual(by_file["003_duplicate_series_snapshot_004.json"]["reason_code"], "duplicate_snapshot_id_in_source_batch")
        self.assertEqual(by_file["004_already_present_series_snapshot_002.json"]["reason_code"], "already_present_in_workspace_inbox")
        self.assertEqual(by_file["005_malformed.json"]["status"], "quarantined")
        self.assertEqual(by_file["006_unsupported.json"]["reason_code"], "unsupported_snapshot_shape")
        self.assertEqual(by_file["007_operator_note.txt"]["reason_code"], "ignored_non_json_file")

    def test_source_file_mode_discovers_one_snapshot(self):
        before = _fixture_file_snapshot()
        payload = json.loads(_run_json("--source", str(SOURCE / "001_series_snapshot_004.json")).stdout)
        self.assertEqual(payload["summary"]["discovered_inputs"], 1)
        self.assertEqual(payload["summary"]["importable_snapshots"], 1)
        self.assertEqual(payload["imported_records"][0]["snapshot_id"], "series_snapshot_004")
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_polymarket_markets_list_shape_imports_as_canonical_snapshot(self):
        before = _fixture_file_snapshot()
        payload = json.loads(_run_json("--source", str(POLYMARKET_FIXTURE)).stdout)
        self.assertEqual(payload["summary"]["discovered_inputs"], 1)
        self.assertEqual(payload["summary"]["importable_snapshots"], 1)
        self.assertEqual(payload["summary"]["skipped_or_quarantined_inputs"], 0)
        self.assertEqual(payload["reason_counts"], {})
        row = payload["imported_records"][0]
        self.assertEqual(row["snapshot_id"], "008_polymarket_markets_active_minimized")
        self.assertEqual(row["source_shape"], "polymarket_gamma_markets_response")
        self.assertEqual(row["source_market_count"], 5)
        self.assertEqual(row["supported_market_count"], 5)
        self.assertEqual(row["unsupported_market_count"], 0)
        self.assertEqual(row["snapshot_markets"], 5)
        self.assertEqual(row["adapter_summary"]["adapted_raw_markets"], 2)
        self.assertEqual(row["adapter_summary"]["adapter_rejections"], 3)
        self.assertEqual(row["adapter_summary"]["rejection_reason_counts"], {"ambiguous_side": 1, "missing_target": 1, "unsupported_asset": 1})
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_polymarket_markets_list_write_inbox_and_manifest(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = _make_workspace(temp_dir)
            out_manifest = Path(temp_dir) / "polymarket_import_manifest.json"
            payload = json.loads(_run_json(
                "--source", str(POLYMARKET_FIXTURE),
                "--workspace", str(workspace),
                "--write-inbox",
                "--out-manifest", str(out_manifest),
            ).stdout)
            self.assertTrue(payload["manifest_written"])
            self.assertEqual(payload["summary"]["imported_snapshots"], 1)
            self.assertEqual(payload["output_inbox_files"][0]["file_name"], "004_008_polymarket_markets_active_minimized.json")
            inbox_payload = json.loads((workspace / "inbox" / "004_008_polymarket_markets_active_minimized.json").read_text(encoding="utf-8"))
            self.assertEqual(inbox_payload["snapshot_id"], "008_polymarket_markets_active_minimized")
            self.assertEqual(inbox_payload["snapshot"]["source_market_count"], 5)
            self.assertEqual(inbox_payload["snapshot"]["supported_market_count"], 5)
            self.assertEqual(len(inbox_payload["snapshot"]["markets"]), 5)
            manifest = json.loads(out_manifest.read_text(encoding="utf-8"))
            self.assertEqual(manifest["imported_records"][0]["snapshot_id"], "008_polymarket_markets_active_minimized")
            self.assertEqual(manifest["imported_records"][0]["source_shape"], "polymarket_gamma_markets_response")
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_polymarket_markets_list_skips_unsupported_individual_markets(self):
        before = _fixture_file_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "polymarket_with_bad_market.json"
            rows = json.loads(POLYMARKET_FIXTURE.read_text(encoding="utf-8"))
            rows.append({
                "id": "unsupported-missing-question",
                "active": True,
                "closed": False,
                "outcomes": "[\"Yes\", \"No\"]",
                "outcomePrices": "[\"0.5\", \"0.5\"]",
                "updatedAt": "2026-04-27T04:35:00Z",
            })
            source.write_text(json.dumps(rows, indent=2), encoding="utf-8")
            payload = json.loads(_run_json("--source", str(source)).stdout)
            row = payload["imported_records"][0]
            self.assertEqual(payload["summary"]["importable_snapshots"], 1)
            self.assertEqual(payload["summary"]["skipped_or_quarantined_inputs"], 0)
            self.assertEqual(row["source_market_count"], 6)
            self.assertEqual(row["supported_market_count"], 5)
            self.assertEqual(row["unsupported_market_count"], 1)
            self.assertEqual(row["skipped_market_count"], 1)
            self.assertEqual(row["snapshot_markets"], 5)
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_canonical_fixture_workspace_has_not_been_mutated(self):
        self.assertEqual(
            sorted(path.name for path in (FIXTURE_WORKSPACE / "inbox").iterdir() if path.is_file()),
            ["001_series_snapshot_001.json", "002_series_snapshot_002.json", "003_series_snapshot_003.json"],
        )
        self.assertFalse((FIXTURE_WORKSPACE / "inbox" / "004_008_polymarket_markets_active_minimized.json").exists())
        self.assertFalse((FIXTURE_WORKSPACE / "inbox" / "004_series_snapshot_004.json").exists())
        self.assertFalse((FIXTURE_WORKSPACE / "inbox" / "005_series_snapshot_005.json").exists())

    def test_existing_manual_workspace_and_lifecycle_commands_still_pass(self):
        workspace_payload = json.loads(subprocess.run([sys.executable, str(MANUAL_WORKSPACE_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        subprocess.run([sys.executable, str(MANUAL_WORKSPACE_RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)
        bundle_payload = json.loads(subprocess.run([sys.executable, str(MANUAL_BUNDLE_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        scenario_payload = json.loads(subprocess.run([sys.executable, str(SCENARIO_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        gates_payload = json.loads(subprocess.run([sys.executable, str(GATES_RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        self.assertTrue(workspace_payload["offline_only"])
        self.assertTrue(bundle_payload["offline_only"])
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
            "prompt_automation_added",
        ):
            self.assertFalse(flags[key])

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
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "re", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
