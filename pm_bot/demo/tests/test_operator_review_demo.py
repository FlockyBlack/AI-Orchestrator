import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "demo" / "run_operator_review_demo.py"
EXPECTED_JSON = ROOT / "pm_bot" / "demo" / "expected_operator_review_demo.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "demo" / "expected_operator_review_demo.v1.md"


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class OperatorReviewDemoTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_demo_is_review_only(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["operator_review_only"])
        self.assertIn("no-action", payload["watchlist_no_action_statement"])

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
