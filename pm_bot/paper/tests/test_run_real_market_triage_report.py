import ast
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_real_market_triage_report.py"
FIXTURE_SOURCE_ARG = r"pm_bot\paper\manual_snapshot_import_source\008_polymarket_markets_active_minimized.fixture.json"
REAL_SOURCE = ROOT / "local_snapshots" / "polymarket_markets_active_001.json"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_real_market_triage_report.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_real_market_triage_report.v1.md"
FIXTURE_WORKSPACE = ROOT / "pm_bot" / "paper" / "manual_paper_workspace"
MANUAL_IMPORT_RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_snapshot_workspace_import.py"
OPERATOR_CYCLE_RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_paper_operator_cycle.py"
LIFECYCLE_GATES_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_regression_gates.py"


def _frag(*parts):
    return "".join(parts)


def _run_json(*args):
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown(*args):
    return subprocess.run([sys.executable, str(RUNNER), "--markdown", *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _fixture_file_snapshot():
    return {
        path.relative_to(FIXTURE_WORKSPACE).as_posix(): path.read_bytes()
        for path in sorted(FIXTURE_WORKSPACE.rglob("*"))
        if path.is_file()
    }


class RunRealMarketTriageReportTests(unittest.TestCase):
    def test_fixture_json_stdout_is_deterministic(self):
        before = _fixture_file_snapshot()
        payload = json.loads(_run_json("--source", FIXTURE_SOURCE_ARG).stdout)
        self.assertEqual(payload, json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))
        self.assertTrue(payload["gamma_market_list_detected"])
        self.assertEqual(payload["summary"]["total_markets_seen"], 5)
        self.assertEqual(payload["summary"]["real_gamma_crypto_numeric_adapted"], 2)
        self.assertEqual(payload["summary"]["adapter_rejection_reason_counts"], {"ambiguous_side": 1, "missing_target": 1, "unsupported_asset": 1})
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_fixture_markdown_stdout_is_deterministic(self):
        before = _fixture_file_snapshot()
        self.assertEqual(_run_markdown("--source", FIXTURE_SOURCE_ARG).stdout, EXPECTED_MD.read_text(encoding="utf-8"))
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_real_local_snapshot_command_runs_if_file_exists(self):
        if not REAL_SOURCE.exists():
            self.skipTest("Real local Polymarket snapshot is not present in this checkout.")
        payload = json.loads(_run_json().stdout)
        summary = payload["summary"]
        self.assertEqual(payload["source_path"], str(REAL_SOURCE))
        self.assertEqual(payload["source_shape"], "polymarket_gamma_markets_response")
        self.assertEqual(payload["top_level_shape"], "top_level_list")
        self.assertEqual(summary["total_markets_seen"], 100)
        self.assertEqual(summary["current_crypto_numeric_actionable"], 0)
        self.assertEqual(summary["adapter_rejection_reason_counts"], {"ambiguous_side": 1, "unsupported_asset": 99})
        self.assertEqual(summary["outcome_shape_counts"], {"yes_no": 100, "up_down": 0, "multi_outcome": 0, "unknown": 0})
        self.assertEqual(summary["top_candidate_count"], 10)

    def test_current_adapter_rejection_counts_are_included(self):
        payload = json.loads(_run_json("--source", FIXTURE_SOURCE_ARG).stdout)
        summary = payload["summary"]
        self.assertIn("adapter_rejection_reason_counts", summary)
        self.assertEqual(summary["current_crypto_numeric_actionable"], 2)
        self.assertEqual(summary["adapter_rejection_reason_counts"], {"ambiguous_side": 1, "missing_target": 1, "unsupported_asset": 1})
        self.assertTrue(all("why_actionable_or_rejected" in row for row in payload["top_candidates"]))

    def test_fixture_supported_examples_convert_to_normalized_scorer_input(self):
        importer = _load_module(ROOT / "pm_bot" / "paper" / "run_manual_snapshot_workspace_import.py", "pmbot_test_gamma_importer")
        adapter = _load_module(ROOT / "pm_bot" / "scoring" / "adapt_live_shaped_crypto_snapshot.py", "pmbot_test_gamma_adapter")
        intake = _load_module(ROOT / "pm_bot" / "scoring" / "crypto_numeric_market_intake.py", "pmbot_test_gamma_intake")
        rows = json.loads((ROOT / FIXTURE_SOURCE_ARG).read_text(encoding="utf-8"))

        adapted = []
        rejections = {}
        for row in rows:
            canonical = importer._polymarket_market_to_canonical(row)
            raw_record, rejection = adapter._adapt_snapshot(canonical)
            if rejection is None:
                adapted.append(raw_record)
            else:
                rejections[rejection["market_id"]] = rejection["reason_code"]

        self.assertEqual(
            [(row["market_id"], row["asset"], row["side_candidate"], row["target_price_candidate"]) for row in adapted],
            [
                ("0xgamma_btc_above_90000", "BTC", "above", 90000.0),
                ("0xgamma_eth_below_3000", "ETH", "below", 3000.0),
            ],
        )
        self.assertEqual(rejections, {
            "0xgamma_non_crypto_numeric": "unsupported_asset",
            "0xgamma_btc_missing_target": "missing_target",
            "0xgamma_eth_ambiguous_side": "ambiguous_side",
        })

        intake_report = intake.build_intake_report({
            "fixture_id": "test_gamma_adapted_raw_markets",
            "raw_markets": adapted,
        })
        self.assertEqual(intake_report["summary"]["normalized_supported"], 2)
        self.assertEqual(
            [(row["market_id"], row["asset"], row["side"], row["target_price"]) for row in intake_report["normalized_scorer_fixture"]["markets"]],
            [
                ("0xgamma_btc_above_90000", "BTC", "above", 90000.0),
                ("0xgamma_eth_below_3000", "ETH", "below", 3000.0),
            ],
        )

    def test_no_state_or_workspace_mutation(self):
        before = _fixture_file_snapshot()
        _run_json("--source", FIXTURE_SOURCE_ARG)
        _run_markdown("--source", FIXTURE_SOURCE_ARG)
        if REAL_SOURCE.exists():
            _run_json()
            _run_markdown()
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_existing_manual_import_operator_cycle_and_lifecycle_gates_still_pass(self):
        if REAL_SOURCE.exists():
            subprocess.run(
                [sys.executable, str(MANUAL_IMPORT_RUNNER), "--source", str(REAL_SOURCE), "--markdown"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
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
        payload = json.loads(_run_json("--source", FIXTURE_SOURCE_ARG).stdout)
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

    def test_no_network_or_runtime_imports(self):
        source = RUNNER.read_text(encoding="utf-8").lower()
        forbidden = [
            _frag("re", "quests"),
            _frag("urllib", ".", "request"),
            "socket",
            "websocket",
            "httpx",
            "aiohttp",
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
