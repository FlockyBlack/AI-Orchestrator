import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MANAGER = ROOT / "codex_auto" / "queue" / "queue_manager.py"
READY_TASK = ROOT / "codex_auto" / "tasks" / "ready" / "CODEX-AUTO-TINY-001.task.json"
RESULT_RECORD = ROOT / "codex_auto" / "tasks" / "needs_flocky_review" / "QUEUE-CODEX-AUTO-TINY-001.result.json"
OUTPUT_PATH = ROOT / "codex_auto" / "runs" / "CODEX-AUTO-TINY-001" / "fixture_output.json"
PMBOT_READY = ROOT / "codex_auto" / "tasks" / "ready" / "PMBOT-005-PAPER-SIMULATION.task.json"


def _run_manager(*args, env=None):
    return subprocess.run(
        [sys.executable, str(MANAGER), *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


class QueueManagerTests(unittest.TestCase):
    def setUp(self):
        self._original_result_record = None
        if RESULT_RECORD.exists():
            self._original_result_record = RESULT_RECORD.read_text(encoding="utf-8")
        RESULT_RECORD.unlink(missing_ok=True)

    def tearDown(self):
        if self._original_result_record is None:
            RESULT_RECORD.unlink(missing_ok=True)
        else:
            RESULT_RECORD.parent.mkdir(parents=True, exist_ok=True)
            RESULT_RECORD.write_text(self._original_result_record, encoding="utf-8")

    def test_list_ready_returns_ready_task(self):
        result = _run_manager("--list-ready")
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(any(item["queue_task_id"] == "QUEUE-CODEX-AUTO-TINY-001" for item in payload["ready_tasks"]))
        self.assertTrue(any(item["codex_task_id"] == "PMBOT-005-PAPER-SIMULATION" for item in payload["ready_tasks"]))

    def test_validate_validates_ready_task(self):
        result = _run_manager("--validate", READY_TASK)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "valid")

    def test_dry_run_next_does_not_move_files_or_execute(self):
        result = _run_manager("--dry-run-next")
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "dry_run_ready")
        self.assertEqual(payload["moved_files"], [])
        self.assertTrue(READY_TASK.exists())
        self.assertFalse(RESULT_RECORD.exists())

    def test_execute_next_controlled_only_for_tiny_and_produces_result_record(self):
        result = _run_manager("--execute-next-controlled")
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(RESULT_RECORD.exists())
        self.assertTrue(READY_TASK.exists())

    def test_result_record_requires_flocky_validation_and_not_final_done(self):
        _run_manager("--execute-next-controlled")
        record = json.loads(RESULT_RECORD.read_text(encoding="utf-8"))
        self.assertTrue(record["flocky_validation_required"])
        self.assertEqual(record["next_queue_state"], "needs_flocky_review")
        serialized = json.dumps(record).lower()
        self.assertNotIn("final done", serialized)

    def test_queue_manager_imports_no_dispatcher_or_run_codex_or_runtime_loop_modules(self):
        source = MANAGER.read_text(encoding="utf-8").lower()
        self.assertNotIn("import dispatcher", source)
        self.assertNotIn("from dispatcher", source)
        self.assertNotIn("import run_codex", source)
        self.assertNotIn("from run_codex", source)
        self.assertNotIn("runtime loop", source)

    def test_queue_manager_does_not_use_network_api_wallet_private_key_or_trading(self):
        source = MANAGER.read_text(encoding="utf-8").lower()
        self.assertNotIn("requests", source)
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("socket", source)

    def test_queue_manager_does_not_mutate_ai_orchestrator_runtime_state(self):
        before = OUTPUT_PATH.read_text(encoding="utf-8")
        _run_manager("--execute-next-controlled")
        after = OUTPUT_PATH.read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def test_invalid_queue_tasks_are_blocked(self):
        bad_task = ROOT / "codex_auto" / "tasks" / "ready" / "tmp_invalid_queue.task.json"
        data = json.loads(READY_TASK.read_text(encoding="utf-8"))
        data["runtime_wiring_allowed"] = True
        bad_task.write_text(json.dumps(data), encoding="utf-8")
        self.addCleanup(lambda: bad_task.unlink(missing_ok=True))
        result = _run_manager("--validate", bad_task)
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "invalid")

    def test_dry_run_next_does_not_execute_pmbot_tasks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_ready_root = Path(temp_dir)
            pmbot_payload = json.loads(PMBOT_READY.read_text(encoding="utf-8"))
            (temp_ready_root / "AAA-PMBOT.task.json").write_text(json.dumps(pmbot_payload), encoding="utf-8")
            env = dict(os.environ)
            env["CODEX_AUTO_READY_ROOT"] = str(temp_ready_root)
            result = _run_manager("--dry-run-next", env=env)
            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(payload["status"], "blocked_preview_only")
            self.assertFalse(payload["would_execute"])

    def test_execute_next_controlled_remains_limited_to_tiny(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_ready_root = Path(temp_dir)
            pmbot_payload = json.loads(PMBOT_READY.read_text(encoding="utf-8"))
            (temp_ready_root / "AAA-PMBOT.task.json").write_text(json.dumps(pmbot_payload), encoding="utf-8")
            env = dict(os.environ)
            env["CODEX_AUTO_READY_ROOT"] = str(temp_ready_root)
            result = _run_manager("--execute-next-controlled", env=env)
            payload = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(payload["status"], "blocked")
            self.assertIn("unsupported_execute_next_controlled_task", payload["errors"])

    def test_standard_library_only(self):
        source = MANAGER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "os", "subprocess", "sys", "datetime", "pathlib"})


if __name__ == "__main__":
    unittest.main()
