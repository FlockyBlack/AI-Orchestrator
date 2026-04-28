import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "operator" / "operator_review_checklist.py"
EXPECTED_JSON = ROOT / "pm_bot" / "operator" / "expected_operator_review_checklist.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "operator" / "expected_operator_review_checklist.v1.md"


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class OperatorReviewChecklistTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_checklist_has_required_steps(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(len(payload["items"]), 12)
        self.assertTrue(all(item["required"] for item in payload["items"]))

    def test_standard_library_only(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib"})


if __name__ == "__main__":
    unittest.main()
