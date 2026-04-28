import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "demo" / "run_adversarial_validation_demo.py"
EXPECTED_JSON = ROOT / "pm_bot" / "demo" / "expected_adversarial_validation_demo.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "demo" / "expected_adversarial_validation_demo.v1.md"


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class AdversarialValidationDemoTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_demo_keeps_false_positive_count_zero(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["false_positive_prevention_report"]["false_positives_count"], 0)
        self.assertTrue(payload["audit_headline"]["static_audit_v4_passed"])

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
