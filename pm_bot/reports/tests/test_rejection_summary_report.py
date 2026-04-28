import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "reports" / "rejection_summary_report.py"
EXPECTED_JSON = ROOT / "pm_bot" / "reports" / "expected_rejection_summary_report.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "reports" / "expected_rejection_summary_report.v1.md"


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class RejectionSummaryReportTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_summary_contains_false_positive_guard(self):
        payload = json.loads(_run_json().stdout)
        self.assertIn("False positives remained at 0", payload["false_positive_prevention_summary"])
        self.assertIn("low_liquidity", payload["liquidity_spread_failures"])

    def test_standard_library_only(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "pathlib"})


if __name__ == "__main__":
    unittest.main()
