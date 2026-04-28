import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "explainability" / "signal_explainer.py"
EXPECTED = ROOT / "pm_bot" / "explainability" / "expected_signal_explanations.v1.json"


def _run():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


class SignalExplainerTests(unittest.TestCase):
    def test_output_matches_expected(self):
        payload = json.loads(_run().stdout)
        expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
        self.assertEqual(payload, expected)

    def test_contains_required_fields(self):
        payload = json.loads(_run().stdout)
        first = payload["explanations"][0]
        self.assertEqual(first["final_decision"], "accept")
        self.assertIn("safety_boundaries", first)
        self.assertIn("no_real_order_statement", first)

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
