import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "scenarios" / "run_demo_scenarios.py"
EXPECTED = ROOT / "pm_bot" / "scenarios" / "expected_demo_scenario_report.v2.json"
SUITE = ROOT / "pm_bot" / "scenarios" / "scenario_suite.v2.json"


def _run_runner():
    return subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


class RunDemoScenariosTests(unittest.TestCase):
    def test_report_matches_expected(self):
        payload = json.loads(_run_runner().stdout)
        expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
        self.assertEqual(payload, expected)

    def test_scenarios_are_fixture_only_and_non_executable(self):
        payload = json.loads(_run_runner().stdout)
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        self.assertEqual(payload["source_type"], "fixture")
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["trading_allowed"])
        self.assertFalse(payload["live_data_allowed"])
        self.assertFalse(payload["wallet_required"])
        self.assertFalse(payload["credential_material_required"])
        for scenario in suite["scenarios"]:
            self.assertEqual(scenario["source_type"], "fixture")
            self.assertFalse(scenario["execution_allowed"])
            self.assertFalse(scenario["trading_allowed"])
            self.assertFalse(scenario["live_data_allowed"])
            self.assertFalse(scenario["wallet_required"])
            self.assertFalse(scenario["credential_material_required"])

    def test_deterministic_output(self):
        first = json.loads(_run_runner().stdout)
        second = json.loads(_run_runner().stdout)
        self.assertEqual(first, second)

    def test_no_network_wallet_or_runtime_imports(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "sys", "pathlib"})
        self.assertTrue(imports.isdisjoint({"requests", "urllib", "socket", "dispatcher", "run_codex", "runtime"}))


if __name__ == "__main__":
    unittest.main()
