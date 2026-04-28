import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "scoring" / "crypto_numeric_market_intake.py"
RAW_FIXTURE = ROOT / "pm_bot" / "scoring" / "crypto_numeric_raw_market_fixtures.v1.json"
EXPECTED_JSON = ROOT / "pm_bot" / "scoring" / "expected_crypto_numeric_intake_report.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "scoring" / "expected_crypto_numeric_intake_report.v1.md"


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER), str(RAW_FIXTURE)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), str(RAW_FIXTURE), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class CryptoNumericMarketIntakeTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_summary_and_supported_assets(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["summary"]["raw_markets"], 11)
        self.assertEqual(payload["summary"]["normalized_supported"], 4)
        self.assertEqual(payload["summary"]["rejected"], 7)
        assets = {row["asset"] for row in payload["normalized_scorer_fixture"]["markets"]}
        sides = {row["side"] for row in payload["normalized_scorer_fixture"]["markets"]}
        self.assertEqual(assets, {"BTC", "ETH"})
        self.assertEqual(sides, {"above", "below"})

    def test_rejection_reason_codes_are_present(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(
            payload["summary"]["rejection_reasons"],
            {
                "ambiguous_settlement": 1,
                "missing_expiry": 1,
                "missing_market_data": 1,
                "missing_target": 1,
                "non_crypto_market": 2,
                "unclear_side": 1,
            },
        )

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["offline_only"])
        self.assertTrue(payload["paper_only"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["trading_allowed"])

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
        self.assertLessEqual(imports, {"argparse", "json", "re", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
