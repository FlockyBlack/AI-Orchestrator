import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "scoring" / "run_crypto_numeric_paper_chain.py"
EXPECTED_JSON = ROOT / "pm_bot" / "scoring" / "expected_crypto_numeric_paper_chain.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "scoring" / "expected_crypto_numeric_paper_chain.v1.md"


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class RunCryptoNumericPaperChainTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_chain_summary(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["score_summary"]["markets_scored"], 4)
        self.assertEqual(payload["review_summary"]["paper_candidates"], 1)
        self.assertEqual(payload["review_summary"]["watchlist"], 1)
        self.assertEqual(payload["review_summary"]["rejected"], 2)
        self.assertEqual(payload["paper_order_summary"]["paper_limit_orders"], 1)
        self.assertEqual(payload["paper_order_summary"]["total_planned_paper_notional"], 100.0)
        self.assertEqual(payload["paper_order_summary"]["max_loss"], 100.0)

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["offline_only"])
        self.assertTrue(payload["paper_only"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["trading_allowed"])
        plan = payload["generated_paper_order_plan"]
        self.assertTrue(plan["offline_only"])
        self.assertTrue(plan["paper_only"])
        self.assertFalse(plan["execution_allowed"])
        self.assertFalse(plan["trading_allowed"])

    def test_no_network_or_runtime_wiring_behavior(self):
        source = RUNNER.read_text(encoding="utf-8").lower()
        forbidden = ["requests", "urllib", "socket", "dispatcher", "run_codex", "submit_order", "execute_trade", "private_key", "api_key"]
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
