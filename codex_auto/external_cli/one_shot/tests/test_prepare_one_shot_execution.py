import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PREPARER = ROOT / "codex_auto" / "external_cli" / "one_shot" / "prepare_one_shot_execution.py"
GATE_PATH = ROOT / "codex_auto" / "external_cli" / "one_shot" / "PMBOT-BATCH-001.one_shot_execution_gate.json"
FINAL_PREVIEW_PATH = ROOT / "codex_auto" / "external_cli" / "one_shot" / "PMBOT-BATCH-001.final_command_preview.txt"


def run_preparer():
    return subprocess.run(
        [sys.executable, str(PREPARER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class PrepareOneShotExecutionTests(unittest.TestCase):
    maxDiff = None

    def test_prepare_creates_gate_and_final_preview(self):
        result = run_preparer()
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(payload["status"], "valid")
        self.assertTrue(GATE_PATH.exists())
        self.assertTrue(FINAL_PREVIEW_PATH.exists())

    def test_gate_flags_are_locked_false_except_human_approval(self):
        run_preparer()
        gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
        self.assertTrue(gate["execution_allowed_by_human"])
        self.assertFalse(gate["execution_allowed_now"])
        self.assertFalse(gate["external_codex_cli_allowed_now"])
        self.assertFalse(gate["generated_prompt_execution_allowed_now"])
        self.assertFalse(gate["runtime_wiring_allowed"])

    def test_final_command_preview_is_manual_run_only(self):
        run_preparer()
        preview = FINAL_PREVIEW_PATH.read_text(encoding="utf-8")
        self.assertIn("MANUAL_RUN_ONLY", preview)
        self.assertIn("DO_NOT_EXECUTE_FROM_THIS_SCRIPT", preview)
        self.assertIn("REQUIRES_POST_EXECUTION_FLOCKY_VALIDATION", preview)
        self.assertIn("NO_RUNTIME_WIRING_ALLOWED", preview)
        self.assertIn("NO_WALLET_API_TRADING", preview)

    def test_preparer_does_not_invoke_external_codex_cli(self):
        source = PREPARER.read_text(encoding="utf-8").lower()
        self.assertNotIn("subprocess", source)
        self.assertNotIn("os.system", source)
        self.assertNotIn("popen", source)

    def test_preparer_does_not_execute_generated_prompt(self):
        source = PREPARER.read_text(encoding="utf-8").lower()
        self.assertNotIn("check_call", source)
        self.assertNotIn("check_output", source)
        self.assertNotIn("run(", source)

    def test_standard_library_only_and_no_runtime_imports(self):
        tree = ast.parse(PREPARER.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertLessEqual(imported, {"json", "sys", "pathlib"})
        self.assertTrue(imported.isdisjoint({"dispatcher", "run_codex", "runtime", "state", "results", "freeze", "checkpoint"}))


if __name__ == "__main__":
    unittest.main()
