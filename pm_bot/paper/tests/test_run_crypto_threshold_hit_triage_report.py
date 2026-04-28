import ast
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_threshold_hit_triage_report.py"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_crypto_threshold_hit_triage_report.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_crypto_threshold_hit_triage_report.v1.md"
REAL_SOURCE = ROOT / "local_snapshots" / "polymarket_markets_active_500_001.json"
REAL_TRIAGE_RUNNER = ROOT / "pm_bot" / "paper" / "run_real_market_triage_report.py"
MANUAL_IMPORT_RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_snapshot_workspace_import.py"
OPERATOR_CYCLE_RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_paper_operator_cycle.py"
LIFECYCLE_GATES_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_regression_gates.py"
FIXTURE_WORKSPACE = ROOT / "pm_bot" / "paper" / "manual_paper_workspace"
SOURCE_SENTINEL = "embedded_crypto_threshold_hit_fixture"


def _frag(*parts):
    return "".join(parts)


def _fixture_rows():
    return [
        {
            "id": "fixture_btc_hit_150k_by_date",
            "conditionId": "0xfixture_btc_hit_150k_by_date",
            "question": "Will BTC hit $150k by June 30, 2026?",
            "slug": "will-btc-hit-150k-by-june-30-2026",
            "active": True,
            "closed": False,
            "outcomes": "[\"Yes\", \"No\"]",
            "outcomePrices": "[\"0.210\", \"0.790\"]",
            "liquidity": 12345.0,
            "liquidityNum": 12345.0,
            "volumeNum": 50000.0,
            "bestBid": 0.2,
            "bestAsk": 0.22,
        },
        {
            "id": "fixture_bitcoin_hit_1m_before_event",
            "conditionId": "0xfixture_bitcoin_hit_1m_before_event",
            "question": "Will Bitcoin hit $1m before GTA VI?",
            "slug": "will-bitcoin-hit-1m-before-gta-vi",
            "active": True,
            "closed": False,
            "outcomes": "[\"Yes\", \"No\"]",
            "outcomePrices": "[\"0.490\", \"0.510\"]",
            "liquidity": 23456.0,
            "liquidityNum": 23456.0,
            "volumeNum": 60000.0,
            "bestBid": 0.48,
            "bestAsk": 0.5,
        },
        {
            "id": "fixture_eth_reach_5000_by_date",
            "conditionId": "0xfixture_eth_reach_5000_by_date",
            "question": "Will ETH reach $5,000 by December 31, 2026?",
            "slug": "will-eth-reach-5000-by-december-31-2026",
            "active": True,
            "closed": False,
            "outcomes": "[\"Yes\", \"No\"]",
            "outcomePrices": "[\"0.330\", \"0.670\"]",
            "liquidity": 34567.0,
            "liquidityNum": 34567.0,
            "volumeNum": 70000.0,
            "bestBid": 0.32,
            "bestAsk": 0.34,
        },
        {
            "id": "fixture_gold_hit_5000_by_date",
            "conditionId": "0xfixture_gold_hit_5000_by_date",
            "question": "Will gold hit $5,000 by December 31, 2026?",
            "slug": "will-gold-hit-5000-by-december-31-2026",
            "active": True,
            "closed": False,
            "outcomes": "[\"Yes\", \"No\"]",
            "outcomePrices": "[\"0.250\", \"0.750\"]",
            "liquidity": 45678.0,
            "liquidityNum": 45678.0,
            "volumeNum": 80000.0,
            "bestBid": 0.24,
            "bestAsk": 0.26,
        },
        {
            "id": "fixture_bitcoin_missing_target",
            "conditionId": "0xfixture_bitcoin_missing_target",
            "question": "Will Bitcoin hit a new all time high by December 31, 2026?",
            "slug": "will-bitcoin-hit-new-all-time-high-by-december-31-2026",
            "active": True,
            "closed": False,
            "outcomes": "[\"Yes\", \"No\"]",
            "outcomePrices": "[\"0.500\", \"0.500\"]",
            "liquidity": 56789.0,
            "liquidityNum": 56789.0,
            "volumeNum": 90000.0,
            "bestBid": 0.49,
            "bestAsk": 0.51,
        },
        {
            "id": "fixture_ambiguous_asset_hit_100000",
            "conditionId": "0xfixture_ambiguous_asset_hit_100000",
            "question": "Will Bitcoin or Ethereum hit $100,000 by December 31, 2026?",
            "slug": "will-bitcoin-or-ethereum-hit-100000-by-december-31-2026",
            "active": True,
            "closed": False,
            "outcomes": "[\"Yes\", \"No\"]",
            "outcomePrices": "[\"0.120\", \"0.880\"]",
            "liquidity": 67890.0,
            "liquidityNum": 67890.0,
            "volumeNum": 100000.0,
            "bestBid": 0.11,
            "bestAsk": 0.13,
        },
    ]


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


def _write_fixture(temp_dir):
    source = Path(temp_dir) / "crypto_threshold_hit_fixture.json"
    source.write_text(json.dumps(_fixture_rows(), indent=2), encoding="utf-8")
    return source


def _normalized_payload(stdout, source):
    payload = json.loads(stdout)
    payload["source_path"] = SOURCE_SENTINEL
    return payload


def _normalized_markdown(stdout, source):
    return stdout.replace(str(source), SOURCE_SENTINEL)


def _fixture_file_snapshot():
    return {
        path.relative_to(FIXTURE_WORKSPACE).as_posix(): path.read_bytes()
        for path in sorted(FIXTURE_WORKSPACE.rglob("*"))
        if path.is_file()
    }


def _utf8_env():
    return {**os.environ, "PYTHONIOENCODING": "utf-8"}


class RunCryptoThresholdHitTriageReportTests(unittest.TestCase):
    def test_fixture_json_stdout_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            first = _run_json("--source", str(source)).stdout
            second = _run_json("--source", str(source)).stdout
            self.assertEqual(first, second)
            payload = _normalized_payload(first, source)
        self.assertEqual(payload, json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))
        self.assertEqual(payload["summary"]["supported_triage_candidates"], 3)
        self.assertEqual(payload["summary"]["reason_counts"], {
            "ambiguous_asset": 1,
            "missing_target": 1,
            "unsupported_asset": 1,
        })

    def test_fixture_markdown_stdout_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            first = _run_markdown("--source", str(source)).stdout
            second = _run_markdown("--source", str(source)).stdout
            self.assertEqual(first, second)
            markdown = _normalized_markdown(first, source)
        self.assertEqual(markdown, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_direct_builder_matches_expected_fixture(self):
        module = _load_module(RUNNER, "pmbot_test_crypto_threshold_hit_triage")
        payload = module.build_crypto_threshold_hit_triage_report(ROOT, SOURCE_SENTINEL, _fixture_rows())
        self.assertEqual(payload, json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_real_local_500_snapshot_command_runs(self):
        payload = json.loads(_run_json().stdout)
        summary = payload["summary"]
        self.assertEqual(payload["source_path"], str(REAL_SOURCE))
        self.assertEqual(summary["total_markets_seen"], 500)
        self.assertEqual(summary["threshold_hit_crypto_candidates_found"], 3)
        self.assertEqual(summary["supported_triage_candidates"], 3)
        self.assertEqual(summary["supported_market_type_counts"], {
            "threshold_hit_by_date": 2,
            "threshold_hit_before_event": 1,
            "ambiguous_threshold_hit": 0,
        })
        self.assertEqual([row["market_id"] for row in payload["candidate_table"]], ["540844", "573655", "573656"])
        self.assertEqual(payload["summary"]["reason_counts"], {})

    def test_no_state_or_workspace_mutation(self):
        before = _fixture_file_snapshot()
        _run_json()
        _run_markdown()
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            _run_json("--source", str(source))
            _run_markdown("--source", str(source))
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_existing_real_import_operator_and_lifecycle_commands_still_pass(self):
        subprocess.run(
            [sys.executable, str(REAL_TRIAGE_RUNNER), "--source", str(REAL_SOURCE), "--markdown"],
            cwd=ROOT,
            env=_utf8_env(),
            capture_output=True,
            text=True,
            check=True,
        )
        subprocess.run(
            [sys.executable, str(MANUAL_IMPORT_RUNNER), "--source", str(REAL_SOURCE), "--markdown"],
            cwd=ROOT,
            env=_utf8_env(),
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

    def test_no_network_or_runtime_behavior(self):
        source = RUNNER.read_text(encoding="utf-8").lower()
        forbidden = [
            _frag("re", "quests"),
            _frag("urllib", ".", "request"),
            "socket",
            "websocket",
            "httpx",
            "aiohttp",
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
        self.assertLessEqual(imports, {"argparse", "json", "re", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
