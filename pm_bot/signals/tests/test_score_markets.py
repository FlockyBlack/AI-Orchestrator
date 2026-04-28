import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCORER = ROOT / "pm_bot" / "signals" / "score_markets.py"
NORMALIZED = ROOT / "pm_bot" / "normalization" / "expected_normalized_market.v1.json"
EXPECTED = ROOT / "pm_bot" / "signals" / "expected_signal_report.v1.json"


def _run_scorer():
    return subprocess.run(
        [sys.executable, str(SCORER), str(NORMALIZED)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


class ScoreMarketsTests(unittest.TestCase):
    def test_signal_report_matches_expected_output(self):
        result = _run_scorer()
        payload = json.loads(result.stdout)
        expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
        self.assertEqual(payload, expected)

    def test_execution_flags_remain_false(self):
        payload = json.loads(_run_scorer().stdout)
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["trading_allowed"])
        self.assertFalse(payload["wallet_required"])
        self.assertFalse(payload["private_key_required"])

    def test_no_network_api_imports(self):
        source = SCORER.read_text(encoding="utf-8")
        self.assertNotIn("requests", source)
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("socket", source)

    def test_no_order_or_execution_behavior(self):
        source = SCORER.read_text(encoding="utf-8").lower()
        self.assertNotIn("submit_order", source)
        self.assertNotIn("execute_trade", source)
        self.assertNotIn("wallet_sign", source)

    def test_deterministic_output(self):
        first = json.loads(_run_scorer().stdout)
        second = json.loads(_run_scorer().stdout)
        self.assertEqual(first, second)

    def test_standard_library_only(self):
        tree = ast.parse(SCORER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
