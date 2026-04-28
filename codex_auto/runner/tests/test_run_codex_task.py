import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "codex_auto" / "runner" / "run_codex_task.py"
FIXTURES = ROOT / "codex_auto" / "fixtures"


def _run_runner(*args):
    return subprocess.run(
        [sys.executable, str(RUNNER), *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class RunCodexTaskTests(unittest.TestCase):
    def test_safe_fixture_returns_dry_run_ready(self):
        result = _run_runner(FIXTURES / "safe_codex_task_fixture.v1.json")
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "dry_run_ready")
        self.assertEqual(payload["execution_mode"], "dry_run")
        self.assertTrue(payload["validation_passed"])

    def test_runner_default_does_not_execute_codex(self):
        result = _run_runner(FIXTURES / "safe_codex_task_fixture.v1.json")
        payload = json.loads(result.stdout)
        self.assertFalse(payload["would_execute"])

    def test_command_preview_is_created(self):
        result = _run_runner(FIXTURES / "safe_codex_task_fixture.v1.json")
        payload = json.loads(result.stdout)
        self.assertIn("codex exec", payload["command_preview"])

    def test_invalid_fixture_returns_invalid(self):
        result = _run_runner(FIXTURES / "invalid_codex_task_forbidden_runtime_touch.v1.json")
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "invalid")

    def test_runner_source_does_not_import_dispatcher_or_run_codex_or_runtime_loop_modules(self):
        source = RUNNER.read_text(encoding="utf-8").lower()
        self.assertNotIn("import dispatcher", source)
        self.assertNotIn("from dispatcher", source)
        self.assertNotIn("import run_codex", source)
        self.assertNotIn("from run_codex", source)
        self.assertNotIn("runtime loop", source)

    def test_runner_does_not_touch_active_tasks_or_network_wallet_trading(self):
        result = _run_runner(FIXTURES / "safe_codex_task_fixture.v1.json")
        payload = json.loads(result.stdout)
        safety = payload["safety_check"]
        self.assertFalse(safety["active_task_files_touched"])
        self.assertFalse(safety["network_used"])
        self.assertFalse(safety["api_used"])
        self.assertFalse(safety["wallet_used"])
        self.assertFalse(safety["private_key_used"])
        self.assertFalse(safety["trading_used"])

    def test_runner_standard_library_only(self):
        source = RUNNER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "shlex", "sys", "datetime", "pathlib", "validate_codex_task"})

    def test_optional_dry_run_result_write_only_under_codex_auto_runs(self):
        task_id = "AI-ORCH-032-WRITE-CHECK"
        fixture_path = ROOT / "codex_auto" / "runs" / "tmp_write_fixture.json"
        task = json.loads((FIXTURES / "safe_codex_task_fixture.v1.json").read_text(encoding="utf-8"))
        task["task_id"] = task_id
        fixture_path.write_text(json.dumps(task), encoding="utf-8")
        result_path = ROOT / "codex_auto" / "runs" / task_id / "dry_run_result.json"

        self.addCleanup(lambda: result_path.parent.rmdir() if result_path.parent.exists() else None)
        self.addCleanup(lambda: result_path.unlink(missing_ok=True))
        self.addCleanup(lambda: fixture_path.unlink(missing_ok=True))

        result = _run_runner("--write-dry-run-result", fixture_path)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(Path(payload["dry_run_result_path"]), result_path)
        self.assertTrue(result_path.exists())
        self.assertIn(str(ROOT / "codex_auto" / "runs"), payload["dry_run_result_path"])


if __name__ == "__main__":
    unittest.main()
