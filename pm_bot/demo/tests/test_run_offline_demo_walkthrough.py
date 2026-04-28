import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "demo" / "run_offline_demo_walkthrough.py"
EXPECTED_JSON = ROOT / "pm_bot" / "demo" / "expected_offline_demo_walkthrough.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "demo" / "expected_offline_demo_walkthrough.v1.md"


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class OfflineDemoWalkthroughTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_walkthrough_preserves_safety_flags(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["offline_only"])
        self.assertTrue(payload["paper_only"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["trading_allowed"])
        self.assertFalse(payload["network_used"])
        self.assertFalse(payload["api_used"])
        self.assertFalse(payload["wallet_used"])
        self.assertFalse(payload["safety_evidence"]["raw_manifest_network_detected"])
        self.assertFalse(payload["safety_evidence"]["raw_manifest_wallet_detected"])
        self.assertFalse(payload["safety_evidence"]["raw_manifest_order_or_trading_detected"])

    def test_walkthrough_runs_existing_child_commands(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(len(payload["commands_run"]), 10)
        self.assertTrue(all(command["status"] == "pass" for command in payload["commands_run"]))
        self.assertIn("run_operator_review_demo.py", payload["commands_run"][0]["command"])

    def test_child_failure_is_not_suppressed(self):
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.run(
                [sys.executable, str(ROOT / "pm_bot" / "paper" / "simulate_paper_plan.py")],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

    def test_standard_library_only(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "subprocess", "sys"})


if __name__ == "__main__":
    unittest.main()
