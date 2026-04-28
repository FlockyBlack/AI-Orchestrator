import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_regression_gates.py"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_crypto_numeric_lifecycle_regression_gates.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_crypto_numeric_lifecycle_regression_gates.v1.md"


def _frag(*parts):
    return "".join(parts)


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class RunCryptoNumericLifecycleRegressionGatesTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_gate_summary(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(
            payload["gates_summary"],
            {
                "gates_checked": 6,
                "gates_passed": 6,
                "gates_failed": 0,
                "safety_flags_locked": True,
                "bad_entries_locked_zero": True,
                "settled_no_fill_guard_locked": True,
            },
        )
        self.assertEqual(payload["status"], "passed")

    def test_locked_replay_summary(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(
            payload["locked_replay_summary"],
            {
                "scenarios": 7,
                "filled_orders": 3,
                "wins": 2,
                "losses": 0,
                "bad_entries": 0,
                "rejected_bad_cases": 1,
                "total_paper_pnl": 179.31,
            },
        )

    def test_required_gates_are_present_and_pass(self):
        payload = json.loads(_run_json().stdout)
        gates = {gate["gate_id"]: gate for gate in payload["gates"]}
        self.assertEqual(
            set(gates),
            {
                "aggregate_outcomes_locked",
                "bad_entries_locked_zero",
                "settled_no_fill_guard_locked",
                "no_action_and_rejected_do_not_order",
                "winning_scenarios_still_fill",
                "safety_flags_locked",
            },
        )
        self.assertTrue(all(gate["passed"] for gate in gates.values()))
        self.assertEqual(gates["settled_no_fill_guard_locked"]["details"]["status"], "not_filled")

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["offline_only"])
        self.assertTrue(payload["paper_only"])
        for key in ("execution_allowed", "trading_allowed", "real_order_created", "wallet_used", "api_used", "network_used"):
            self.assertFalse(payload[key])

    def test_no_runtime_or_network_behavior(self):
        source = RUNNER.read_text(encoding="utf-8").lower()
        forbidden = [
            _frag("re", "quests"),
            _frag("urllib", ".", "request"),
            "socket",
            _frag("dispatch", "er"),
            _frag("run", "_", "codex"),
            _frag("private", "_", "key"),
            _frag("submit", "_", "order"),
            _frag("execute", "_", "trade"),
        ]
        for term in forbidden:
            self.assertNotIn(term, source)

    def test_standard_library_only(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
