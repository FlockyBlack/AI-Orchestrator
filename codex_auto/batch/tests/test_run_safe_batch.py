import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BATCH = ROOT / "codex_auto" / "batch" / "run_safe_batch.py"
DONE_REVIEW = ROOT / "codex_auto" / "tasks" / "done" / "FLOCKY-REVIEW-QUEUE-CODEX-AUTO-TINY-001.review.json"
RESULT_RECORD = ROOT / "codex_auto" / "tasks" / "needs_flocky_review" / "QUEUE-CODEX-AUTO-TINY-001.result.json"
PMBOT_READY = "codex_auto/tasks/ready/PMBOT-005-PAPER-SIMULATION.task.json"


def _run_batch(*args):
    return subprocess.run(
        [sys.executable, str(BATCH), *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class RunSafeBatchTests(unittest.TestCase):
    def setUp(self):
        self._original_done = None
        if DONE_REVIEW.exists():
            self._original_done = DONE_REVIEW.read_text(encoding="utf-8")
        DONE_REVIEW.unlink(missing_ok=True)

    def tearDown(self):
        if self._original_done is None:
            DONE_REVIEW.unlink(missing_ok=True)
        else:
            DONE_REVIEW.parent.mkdir(parents=True, exist_ok=True)
            DONE_REVIEW.write_text(self._original_done, encoding="utf-8")

    def test_dry_run_does_not_execute_or_write(self):
        result = _run_batch("--max-tasks", "1", "--dry-run")
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["mode"], "dry_run")
        self.assertFalse(payload["flocky_review_written"])
        self.assertFalse(DONE_REVIEW.exists())
        self.assertIn(PMBOT_READY, payload["tasks_seen"])

    def test_execute_controlled_works_only_for_tiny(self):
        result = _run_batch("--max-tasks", "1", "--execute-controlled")
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertIn("queue_execute_next_controlled", payload["actions_taken"])
        self.assertTrue(RESULT_RECORD.exists())
        self.assertEqual(payload["queue_manager_result"]["codex_task_id"], "CODEX-AUTO-TINY-001")

    def test_execute_controlled_with_flocky_review_writes_done_review(self):
        result = _run_batch("--max-tasks", "1", "--execute-controlled", "--flocky-review")
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(payload["flocky_review_written"])
        self.assertTrue(DONE_REVIEW.exists())

    def test_max_tasks_gt_one_is_blocked(self):
        result = _run_batch("--max-tasks", "2", "--dry-run")
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "blocked")

    def test_done_review_does_not_claim_final_flocky_done(self):
        _run_batch("--max-tasks", "1", "--execute-controlled", "--flocky-review")
        payload = json.loads(DONE_REVIEW.read_text(encoding="utf-8"))
        self.assertFalse(payload["final_flocky_done_claimed"])

    def test_batch_output_has_false_safety_flags(self):
        payload = json.loads(_run_batch("--max-tasks", "1", "--dry-run").stdout)
        safety = payload["safety_check"]
        self.assertFalse(safety["runtime_changed"])
        self.assertFalse(safety["dispatcher_touched"])
        self.assertFalse(safety["run_codex_touched"])
        self.assertFalse(safety["network_used"])
        self.assertFalse(safety["api_used"])
        self.assertFalse(safety["wallet_used"])
        self.assertFalse(safety["private_key_used"])
        self.assertFalse(safety["trading_used"])
        self.assertTrue(safety["single_runtime_source_rule_preserved"])

    def test_batch_dry_run_does_not_execute_pmbot_tasks(self):
        payload = json.loads(_run_batch("--max-tasks", "1", "--dry-run").stdout)
        self.assertFalse(payload["queue_manager_result"]["would_execute"])
        self.assertNotEqual(payload["queue_manager_result"]["codex_task_id"], "PMBOT-005-PAPER-SIMULATION")

    def test_no_external_codex_cli_or_runtime_imports(self):
        source = BATCH.read_text(encoding="utf-8").lower()
        self.assertNotIn("import dispatcher", source)
        self.assertNotIn("from dispatcher", source)
        self.assertNotIn("import run_codex", source)
        self.assertNotIn("from run_codex", source)
        self.assertNotIn("runtime loop", source)
        self.assertNotIn("codex exec", source)
        self.assertNotIn("requests", source)
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("socket", source)

    def test_standard_library_only(self):
        source = BATCH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "subprocess", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
