import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_live_shaped_snapshot_paper_lifecycle.py"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_live_shaped_snapshot_paper_lifecycle.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_live_shaped_snapshot_paper_lifecycle.v1.md"
SNAPSHOT_FIXTURE = ROOT / "pm_bot" / "scoring" / "crypto_numeric_live_shaped_snapshot_fixture.v1.json"


def _frag(*parts):
    return "".join(parts)


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_snapshot(path):
    return subprocess.run([sys.executable, str(RUNNER), "--snapshot", str(path)], cwd=ROOT, capture_output=True, text=True, check=True)


class RunLiveShapedSnapshotPaperLifecycleTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_explicit_snapshot_fixture_matches_default_output(self):
        self.assertEqual(json.loads(_run_snapshot(SNAPSHOT_FIXTURE).stdout), json.loads(_run_json().stdout))

    def test_invalid_snapshot_path_fails_cleanly(self):
        missing = ROOT / "pm_bot" / "scoring" / "missing_live_snapshot_fixture.json"
        result = subprocess.run([sys.executable, str(RUNNER), "--snapshot", str(missing)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("error: --snapshot path does not exist:", result.stderr)

    def test_lifecycle_summary(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(
            payload["lifecycle_summary"],
            {
                "snapshot_markets": 10,
                "adapted_raw_markets": 3,
                "adapter_rejections": 7,
                "normalized_supported": 3,
                "intake_rejections": 0,
                "markets_scored": 3,
                "paper_candidates": 1,
                "watchlist": 1,
                "rejected_after_scoring": 1,
                "paper_orders_submitted": 1,
                "paper_orders_filled": 1,
                "open_positions": 0,
                "settled_positions": 1,
                "total_paper_notional": 100.0,
                "total_max_loss": 100.0,
                "paper_pnl": 72.41,
                "no_action_entries": 2,
            },
        )

    def test_adapter_and_intake_rejections_are_preserved(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(len(payload["adapter_rejections"]), 7)
        self.assertEqual(payload["rejected_raw_markets"], [])
        self.assertEqual(
            {row["reason_code"] for row in payload["adapter_rejections"]},
            {
                "missing_question",
                "missing_market_id",
                "missing_price",
                "missing_liquidity",
                "missing_expiry",
                "unsupported_asset",
                "ambiguous_side",
            },
        )

    def test_paper_lifecycle_artifacts_are_included(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(len(payload["paper_candidate_rows"]), 1)
        self.assertEqual(len(payload["watchlist_rows"]), 1)
        self.assertEqual(len(payload["scoring_rejections"]), 1)
        self.assertEqual(payload["paper_positions"][0]["market_id"], "live_btc_above_90000_2026_05_31")
        self.assertEqual(payload["paper_positions"][0]["status"], "settled")
        self.assertEqual(payload["generated_paper_order_plan"]["paper_order_count"], 1)

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["offline_only"])
        self.assertTrue(payload["paper_only"])
        for key in (
            "live_fetcher_implemented",
            "network_used",
            "api_used",
            "credentials_used",
            "wallet_used",
            "real_order_created",
            "trading_allowed",
        ):
            self.assertFalse(payload[key])
            self.assertFalse(payload["portfolio_exposure_summary"][key])

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
