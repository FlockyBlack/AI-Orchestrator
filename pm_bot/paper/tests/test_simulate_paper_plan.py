import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SIMULATOR = ROOT / "pm_bot" / "paper" / "simulate_paper_plan.py"
FIXTURE = ROOT / "pm_bot" / "paper" / "paper_plan_fixture.v1.json"
EXPECTED = ROOT / "pm_bot" / "paper" / "expected_paper_simulation.v1.json"


def _frag(*parts):
    return "".join(parts)


def _run_simulator():
    return subprocess.run(
        [sys.executable, str(SIMULATOR), str(FIXTURE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


class SimulatePaperPlanTests(unittest.TestCase):
    def test_matches_expected_output(self):
        payload = json.loads(_run_simulator().stdout)
        expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
        self.assertEqual(payload, expected)

    def test_execution_flags_remain_false(self):
        payload = json.loads(_run_simulator().stdout)
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["trading_allowed"])
        self.assertFalse(payload["custody_access_required"])
        self.assertFalse(payload["credential_material_required"])

    def test_deterministic_output(self):
        first = json.loads(_run_simulator().stdout)
        second = json.loads(_run_simulator().stdout)
        self.assertEqual(first, second)

    def test_no_runtime_or_network_behavior(self):
        source = SIMULATOR.read_text(encoding="utf-8").lower()
        self.assertNotIn(_frag("re", "quests"), source)
        self.assertNotIn(_frag("urllib", ".", "request"), source)
        self.assertNotIn(_frag("dispatch", "er"), source)
        self.assertNotIn(_frag("run", "_", "codex"), source)
        self.assertNotIn("subprocess", source)

    def test_standard_library_only(self):
        tree = ast.parse(SIMULATOR.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
