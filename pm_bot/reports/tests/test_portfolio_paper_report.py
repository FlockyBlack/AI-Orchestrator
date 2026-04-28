import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "reports" / "portfolio_paper_report.py"
EXPECTED_JSON = ROOT / "pm_bot" / "reports" / "expected_portfolio_paper_report.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "reports" / "expected_portfolio_paper_report.v1.md"


def _run_json():
    return subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _run_markdown():
    return subprocess.run(
        [sys.executable, str(RUNNER), "--markdown"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


class PortfolioPaperReportTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        payload = json.loads(_run_json().stdout)
        expected = json.loads(EXPECTED_JSON.read_text(encoding="utf-8"))
        self.assertEqual(payload, expected)

    def test_markdown_output_matches_expected(self):
        rendered = _run_markdown().stdout
        expected = EXPECTED_MD.read_text(encoding="utf-8")
        self.assertEqual(rendered, expected)

    def test_key_portfolio_fields(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["total_paper_capital_usd"], 1000.0)
        self.assertEqual(payload["allocated_paper_capital_usd"], 760.0)
        self.assertEqual(payload["paper_position_count"], 4)
        self.assertIn("category_concentration:macro", payload["concentration_warnings"])
        self.assertFalse(payload["network_used"])
        self.assertFalse(payload["wallet_used"])

    def test_standard_library_only(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "pathlib"})
        self.assertTrue(imports.isdisjoint({"requests", "urllib", "socket", "dispatcher", "run_codex", "runtime"}))


if __name__ == "__main__":
    unittest.main()
