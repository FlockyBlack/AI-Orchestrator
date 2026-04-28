import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "demo" / "run_paper_research_demo.py"
EXPECTED_JSON = ROOT / "pm_bot" / "demo" / "expected_paper_research_demo.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "demo" / "expected_paper_research_demo.v1.md"


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


class RunPaperResearchDemoTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        payload = json.loads(_run_json().stdout)
        expected = json.loads(EXPECTED_JSON.read_text(encoding="utf-8"))
        self.assertEqual(payload, expected)

    def test_markdown_output_matches_expected(self):
        rendered = _run_markdown().stdout
        expected = EXPECTED_MD.read_text(encoding="utf-8")
        self.assertEqual(rendered, expected)

    def test_deterministic_output(self):
        first = json.loads(_run_json().stdout)
        second = json.loads(_run_json().stdout)
        self.assertEqual(first, second)
        self.assertEqual(_run_markdown().stdout, _run_markdown().stdout)

    def test_safety_flags_remain_false(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["research_only"])
        self.assertTrue(payload["paper_only"])
        self.assertFalse(payload["live_data_used"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["trading_allowed"])
        self.assertFalse(payload["network_used"])
        self.assertFalse(payload["api_used"])
        self.assertFalse(payload["wallet_used"])
        self.assertFalse(payload["credential_material_required"])
        self.assertFalse(payload["final_flocky_done_claimed"])
        self.assertFalse(payload["runtime_wiring_added"])

    def test_standard_library_only_and_no_forbidden_imports(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "pathlib"})
        self.assertTrue(imports.isdisjoint({"requests", "urllib", "socket", "dispatcher", "run_codex", "runtime", "subprocess"}))


if __name__ == "__main__":
    unittest.main()
