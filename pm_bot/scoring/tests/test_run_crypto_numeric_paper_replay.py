import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "scoring" / "run_crypto_numeric_paper_replay.py"
EXPECTED_JSON = ROOT / "pm_bot" / "scoring" / "expected_crypto_numeric_paper_replay.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "scoring" / "expected_crypto_numeric_paper_replay.v1.md"


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class RunCryptoNumericPaperReplayTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_replay_summary(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(
            payload["summary"],
            {
                "replay_cases": 5,
                "paper_orders": 1,
                "wins": 1,
                "losses": 0,
                "no_action": 4,
                "total_paper_pnl": 69.49,
                "false_positive_or_bad_entry": 0,
                "rejected_bad_cases": 2,
            },
        )

    def test_known_bad_entry_is_no_longer_a_paper_order(self):
        payload = json.loads(_run_json().stdout)
        row = next(item for item in payload["replay_rows"] if item["market_id"] == "replay_btc_above_100000_false_positive_loss")
        self.assertEqual(row["decision"], "watchlist")
        self.assertEqual(row["action"], "no_action")
        self.assertEqual(row["simulated_result"], "no_fill_or_no_action")

    def test_legitimate_candidate_is_preserved(self):
        payload = json.loads(_run_json().stdout)
        row = next(item for item in payload["replay_rows"] if item["market_id"] == "replay_btc_above_90000_win")
        self.assertEqual(row["decision"], "paper_candidate")
        self.assertEqual(row["action"], "paper_limit_order")
        self.assertEqual(row["simulated_result"], "win")

    def test_rejected_bad_cases_remain_no_action(self):
        payload = json.loads(_run_json().stdout)
        rejected_bad = [
            item
            for item in payload["replay_rows"]
            if item["market_id"] in {"replay_btc_above_90000_low_liquidity_loss", "replay_eth_below_3000_wide_spread_loss"}
        ]
        self.assertEqual({item["decision"] for item in rejected_bad}, {"reject"})
        self.assertEqual({item["action"] for item in rejected_bad}, {"no_action"})

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["offline_only"])
        self.assertTrue(payload["paper_only"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["trading_allowed"])
        for row in payload["replay_rows"]:
            self.assertTrue(row["offline_only"])
            self.assertTrue(row["paper_only"])
            self.assertFalse(row["execution_allowed"])
            self.assertFalse(row["trading_allowed"])

    def test_no_network_or_runtime_terms(self):
        source = RUNNER.read_text(encoding="utf-8").lower()
        forbidden = ["requests", "urllib", "socket", "dispatcher", "run_codex", "submit_order", "execute_trade", "private_key", "api_key"]
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
