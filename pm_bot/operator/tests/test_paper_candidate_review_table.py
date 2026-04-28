import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "operator" / "paper_candidate_review_table.py"
EXPECTED_JSON = ROOT / "pm_bot" / "operator" / "expected_paper_candidate_review_table.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "operator" / "expected_paper_candidate_review_table.v1.md"


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run([sys.executable, str(RUNNER), "--markdown"], cwd=ROOT, capture_output=True, text=True, check=True)


class PaperCandidateReviewTableTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_operator_actions_are_non_executable(self):
        payload = json.loads(_run_json().stdout)
        actions = {row["operator_action"] for row in payload["rows"]}
        self.assertLessEqual(actions, {"review_only", "reject_no_action", "watchlist_no_action", "paper_monitor_no_action"})
        self.assertIn("No buy, sell, trade, submit_order, execute, live_action, or real_position behavior exists.", payload["explicit_no_execution_statement"])

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
