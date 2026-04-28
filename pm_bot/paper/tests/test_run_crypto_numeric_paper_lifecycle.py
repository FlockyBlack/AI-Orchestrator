import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_paper_lifecycle.py"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_crypto_numeric_paper_lifecycle.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_crypto_numeric_paper_lifecycle.v1.md"


def _frag(*parts):
    return "".join(parts)


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class RunCryptoNumericPaperLifecycleTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_lifecycle_summary(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(
            payload["lifecycle_summary"],
            {
                "raw_markets": 11,
                "normalized_supported": 4,
                "rejected_raw_markets": 7,
                "markets_scored": 4,
                "paper_candidates": 1,
                "watchlist": 1,
                "rejected_after_scoring": 2,
                "paper_orders_submitted": 1,
                "paper_orders_filled": 1,
                "open_positions": 0,
                "settled_positions": 1,
                "total_paper_notional": 100.0,
                "total_max_loss": 100.0,
                "paper_pnl": 72.41,
                "no_action_entries": 3,
            },
        )

    def test_rejections_and_positions_are_included(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(len(payload["rejected_raw_markets"]), 7)
        self.assertEqual(len(payload["scoring_rejections"]), 2)
        self.assertEqual(len(payload["paper_positions"]), 1)
        self.assertEqual(payload["paper_positions"][0]["market_id"], "raw_btc_above_90000_2026_05_31")
        self.assertEqual(payload["paper_positions"][0]["status"], "settled")

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["offline_only"])
        self.assertTrue(payload["paper_only"])
        for key in ("execution_allowed", "trading_allowed", "real_order_created", "wallet_used", "api_used", "network_used"):
            self.assertFalse(payload[key])
        exposure = payload["portfolio_exposure_summary"]
        self.assertTrue(exposure["offline_only"])
        self.assertTrue(exposure["paper_only"])
        self.assertFalse(exposure["execution_allowed"])
        self.assertFalse(exposure["trading_allowed"])
        self.assertFalse(exposure["real_order_created"])
        self.assertFalse(exposure["wallet_used"])
        self.assertFalse(exposure["api_used"])
        self.assertFalse(exposure["network_used"])

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
