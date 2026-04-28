import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCORER = ROOT / "pm_bot" / "scoring" / "crypto_numeric_market_scorer.py"
FIXTURE = ROOT / "pm_bot" / "scoring" / "crypto_numeric_fixture.v1.json"
EXPECTED = ROOT / "pm_bot" / "scoring" / "expected_crypto_numeric_score_report.v1.json"


def _run_scorer():
    return subprocess.run(
        [sys.executable, str(SCORER), str(FIXTURE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


class CryptoNumericMarketScorerTests(unittest.TestCase):
    def test_score_report_matches_expected_output(self):
        payload = json.loads(_run_scorer().stdout)
        expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
        self.assertEqual(payload, expected)

    def test_required_decision_paths_are_covered(self):
        payload = json.loads(_run_scorer().stdout)
        decisions = {item["decision"] for item in payload["scores"]}
        self.assertEqual(decisions, {"paper_candidate", "watchlist", "reject"})

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_scorer().stdout)
        self.assertTrue(payload["offline_only"])
        self.assertTrue(payload["paper_only"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["trading_allowed"])
        for item in payload["scores"]:
            self.assertTrue(item["offline_only"])
            self.assertTrue(item["paper_only"])
            self.assertFalse(item["execution_allowed"])
            self.assertFalse(item["trading_allowed"])

    def test_deterministic_output(self):
        first = json.loads(_run_scorer().stdout)
        second = json.loads(_run_scorer().stdout)
        self.assertEqual(first, second)

    def test_no_network_api_imports(self):
        source = SCORER.read_text(encoding="utf-8")
        self.assertNotIn("requests", source)
        self.assertNotIn("urllib", source)
        self.assertNotIn("socket", source)
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"json", "sys", "pathlib"})

    def test_no_order_wallet_or_live_execution_behavior(self):
        source = SCORER.read_text(encoding="utf-8").lower()
        forbidden = [
            "submit_order",
            "execute_trade",
            "wallet",
            "private_key",
            "api_key",
            "credential",
            "live_trading",
        ]
        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
