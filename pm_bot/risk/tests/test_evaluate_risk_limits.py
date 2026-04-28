import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVALUATOR = ROOT / "pm_bot" / "risk" / "evaluate_risk_limits.py"
FIXTURE = ROOT / "pm_bot" / "risk" / "risk_fixture.v1.json"
EXPECTED = ROOT / "pm_bot" / "risk" / "expected_risk_report.v1.json"


def _frag(*parts):
    return "".join(parts)


def _run_evaluator():
    return subprocess.run(
        [sys.executable, str(EVALUATOR), str(FIXTURE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


class EvaluateRiskLimitsTests(unittest.TestCase):
    def test_matches_expected_output(self):
        payload = json.loads(_run_evaluator().stdout)
        expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
        self.assertEqual(payload, expected)

    def test_breach_prevents_approval(self):
        payload = json.loads(_run_evaluator().stdout)
        self.assertIn("max_total_notional", payload["breaches"])
        self.assertFalse(payload["approved"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["trading_allowed"])

    def test_deterministic_output(self):
        first = json.loads(_run_evaluator().stdout)
        second = json.loads(_run_evaluator().stdout)
        self.assertEqual(first, second)

    def test_no_runtime_network_or_wallet_behavior(self):
        source = EVALUATOR.read_text(encoding="utf-8").lower()
        self.assertNotIn(_frag("re", "quests"), source)
        self.assertNotIn(_frag("wallet"), source)
        self.assertNotIn(_frag("private", "_", "key"), source)
        self.assertNotIn(_frag("dispatch", "er"), source)
        self.assertNotIn(_frag("run", "_", "codex"), source)

    def test_standard_library_only(self):
        tree = ast.parse(EVALUATOR.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
