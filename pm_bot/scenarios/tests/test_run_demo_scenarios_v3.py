import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "scenarios" / "run_demo_scenarios_v3.py"
EXPECTED = ROOT / "pm_bot" / "scenarios" / "expected_demo_scenario_report.v3.json"


def _run_runner():
    return subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


class RunDemoScenariosV3Tests(unittest.TestCase):
    def test_report_matches_expected(self):
        payload = json.loads(_run_runner().stdout)
        expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
        self.assertEqual(payload, expected)

    def test_safety_and_counts(self):
        payload = json.loads(_run_runner().stdout)
        self.assertTrue(payload["fixture_only"])
        self.assertTrue(payload["paper_only"])
        self.assertTrue(payload["local_only"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["trading_allowed"])
        self.assertEqual(payload["fixture_market_count"], 8)
        self.assertEqual(payload["scenario_count"], 12)
        self.assertEqual(payload["accepted_paper_candidates"], 4)
        self.assertEqual(payload["rejected_paper_candidates"], 3)

    def test_deterministic_output(self):
        first = json.loads(_run_runner().stdout)
        second = json.loads(_run_runner().stdout)
        self.assertEqual(first, second)

    def test_standard_library_only_and_no_forbidden_imports(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "sys", "pathlib"})
        self.assertTrue(imports.isdisjoint({"requests", "urllib", "socket", "dispatcher", "run_codex", "runtime"}))


if __name__ == "__main__":
    unittest.main()
