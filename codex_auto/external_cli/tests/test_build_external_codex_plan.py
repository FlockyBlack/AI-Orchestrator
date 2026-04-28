import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUILDER = ROOT / "codex_auto" / "external_cli" / "build_external_codex_plan.py"
PLAN = ROOT / "codex_auto" / "external_cli" / "plans" / "PMBOT-BATCH-001.external_codex_plan.json"
PREVIEW = ROOT / "codex_auto" / "external_cli" / "plans" / "PMBOT-BATCH-001.command_preview.txt"


def _run_builder():
    return subprocess.run(
        [sys.executable, str(BUILDER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class BuildExternalCodexPlanTests(unittest.TestCase):
    def test_build_external_codex_plan_creates_plan_and_preview_only(self):
        result = _run_builder()
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "valid")
        self.assertTrue(PLAN.exists())
        self.assertTrue(PREVIEW.exists())

    def test_command_preview_exists_but_is_marked_do_not_execute_now(self):
        _run_builder()
        preview = PREVIEW.read_text(encoding="utf-8").lower()
        self.assertIn("preview_only", preview)
        self.assertIn("do_not_execute_now", preview)

    def test_execution_allowed_now_false(self):
        _run_builder()
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        self.assertFalse(plan["execution_allowed_now"])

    def test_external_codex_cli_allowed_now_false(self):
        _run_builder()
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        self.assertFalse(plan["external_codex_cli_allowed_now"])

    def test_requires_human_approval(self):
        _run_builder()
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        self.assertTrue(plan["requires_human_approval_before_execution"])

    def test_requires_flocky_review(self):
        _run_builder()
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        self.assertTrue(plan["requires_flocky_review_before_execution"])

    def test_plan_builder_does_not_execute_generated_prompt(self):
        source = BUILDER.read_text(encoding="utf-8").lower()
        self.assertNotIn("subprocess", source)
        self.assertNotIn("popen", source)
        self.assertNotIn("os.system", source)

    def test_plan_builder_does_not_invoke_external_codex_cli(self):
        source = BUILDER.read_text(encoding="utf-8").lower()
        self.assertNotIn("check_call", source)
        self.assertNotIn("check_output", source)

    def test_standard_library_only(self):
        source = BUILDER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
