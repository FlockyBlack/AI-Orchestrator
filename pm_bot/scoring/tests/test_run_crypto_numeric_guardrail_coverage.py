import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "scoring" / "run_crypto_numeric_guardrail_coverage.py"
EXPECTED_JSON = ROOT / "pm_bot" / "scoring" / "expected_crypto_numeric_guardrail_coverage.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "scoring" / "expected_crypto_numeric_guardrail_coverage.v1.md"


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class RunCryptoNumericGuardrailCoverageTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_guardrail_blocks_only_intended_shape(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(
            payload["coverage_summary"],
            {
                "coverage_cases": 6,
                "guardrail_triggered": 2,
                "paper_candidates_preserved": 4,
                "watchlist_caps": 2,
                "unexpected_blocks": 0,
                "unexpected_allows": 0,
            },
        )

    def test_legitimate_candidate_is_preserved(self):
        payload = json.loads(_run_json().stdout)
        row = next(item for item in payload["coverage_rows"] if item["case_id"] == "clear_legitimate_candidate")
        self.assertEqual(row["actual_decision"], "paper_candidate")
        self.assertEqual(row["unexpected_block"], False)

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["offline_only"])
        self.assertTrue(payload["paper_only"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["trading_allowed"])
        for row in payload["coverage_rows"]:
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
