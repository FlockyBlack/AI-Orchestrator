import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DASHBOARD = ROOT / "pm_bot" / "reports" / "build_research_dashboard.py"
FIXTURE = ROOT / "pm_bot" / "reports" / "dashboard_fixture.v1.json"
EXPECTED = ROOT / "pm_bot" / "reports" / "expected_dashboard_report.v1.json"


def _frag(*parts):
    return "".join(parts)


def _run_dashboard():
    return subprocess.run(
        [sys.executable, str(DASHBOARD), str(FIXTURE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


class BuildResearchDashboardTests(unittest.TestCase):
    def test_matches_expected_output(self):
        payload = json.loads(_run_dashboard().stdout)
        expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
        self.assertEqual(payload, expected)

    def test_safety_gates_remain_blocking(self):
        payload = json.loads(_run_dashboard().stdout)
        self.assertTrue(payload["safety_gates"]["research_only"])
        self.assertTrue(payload["safety_gates"]["execution_blocked"])
        self.assertFalse(payload["trading_allowed"])

    def test_deterministic_output(self):
        first = json.loads(_run_dashboard().stdout)
        second = json.loads(_run_dashboard().stdout)
        self.assertEqual(first, second)

    def test_no_runtime_network_or_wallet_behavior(self):
        source = DASHBOARD.read_text(encoding="utf-8").lower()
        self.assertNotIn(_frag("re", "quests"), source)
        self.assertNotIn(_frag("wallet"), source)
        self.assertNotIn(_frag("private", "_", "key"), source)
        self.assertNotIn(_frag("dispatch", "er"), source)
        self.assertNotIn(_frag("run", "_", "codex"), source)

    def test_standard_library_only(self):
        tree = ast.parse(DASHBOARD.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
