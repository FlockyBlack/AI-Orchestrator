import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "scoring" / "crypto_numeric_review_table.py"
SCORE_REPORT = ROOT / "pm_bot" / "scoring" / "expected_crypto_numeric_score_report.v1.json"
EXPECTED_JSON = ROOT / "pm_bot" / "scoring" / "expected_crypto_numeric_review_table.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "scoring" / "expected_crypto_numeric_review_table.v1.md"


def _run_json():
    return subprocess.run(
        [sys.executable, str(RUNNER), str(SCORE_REPORT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _run_markdown():
    return subprocess.run(
        [sys.executable, str(RUNNER), str(SCORE_REPORT), "--markdown"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


class CryptoNumericReviewTableTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_group_counts_cover_required_decisions(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["group_counts"], {"paper_candidate": 1, "watchlist": 1, "reject": 2})

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["offline_only"])
        self.assertTrue(payload["paper_only"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["trading_allowed"])
        self.assertTrue(payload["operator_review_only"])

    def test_standard_library_only_and_no_network_imports(self):
        source = RUNNER.read_text(encoding="utf-8")
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
        self.assertLessEqual(imports, {"argparse", "json", "sys", "pathlib"})

    def test_no_order_or_live_execution_behavior(self):
        source = RUNNER.read_text(encoding="utf-8").lower()
        forbidden = ["submit_order", "execute_trade", "private_key", "api_key", "live_trading"]
        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
