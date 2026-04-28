import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "quality" / "confidence_breakdown.py"
EXPECTED = ROOT / "pm_bot" / "quality" / "expected_confidence_breakdown.v1.json"


def _run():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


class ConfidenceBreakdownTests(unittest.TestCase):
    def test_output_matches_expected(self):
        self.assertEqual(json.loads(_run().stdout), json.loads(EXPECTED.read_text(encoding="utf-8")))

    def test_breakdown_has_expected_bands(self):
        payload = json.loads(_run().stdout)
        self.assertEqual(payload["confidence_band_counts"]["reject"], 6)
        self.assertEqual(payload["confidence_band_counts"]["high"], 1)

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
