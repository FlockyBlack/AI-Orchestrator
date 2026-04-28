import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONSUMER = ROOT / "codex_auto" / "flocky_review" / "review_needs_flocky.py"
RESULT_RECORD = ROOT / "codex_auto" / "tasks" / "needs_flocky_review" / "QUEUE-CODEX-AUTO-TINY-001.result.json"
READY_TASK = ROOT / "codex_auto" / "tasks" / "ready" / "CODEX-AUTO-TINY-001.task.json"
DONE_REVIEW = ROOT / "codex_auto" / "tasks" / "done" / "FLOCKY-REVIEW-QUEUE-CODEX-AUTO-TINY-001.review.json"
ARTIFACT = ROOT / "codex_auto" / "runs" / "CODEX-AUTO-TINY-001" / "fixture_output.json"


def _run_consumer(*args):
    return subprocess.run(
        [sys.executable, str(CONSUMER), *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ReviewNeedsFlockyTests(unittest.TestCase):
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

    def test_existing_result_is_reviewed_as_pass(self):
        result = _run_consumer(RESULT_RECORD)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["review_status"], "pass")
        self.assertEqual(payload["allowed_next_queue_state"], "done")

    def test_review_requires_durable_fixture_output(self):
        original = ARTIFACT.read_text(encoding="utf-8")
        ARTIFACT.unlink()
        self.addCleanup(lambda: ARTIFACT.write_text(original, encoding="utf-8"))
        result = _run_consumer(RESULT_RECORD)
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["review_status"], "fail")
        self.assertIn("durable_artifact", payload["validation_findings"])

    def test_review_output_has_required_false_flags(self):
        payload = json.loads(_run_consumer(RESULT_RECORD).stdout)
        self.assertFalse(payload["final_flocky_done_claimed"])
        self.assertFalse(payload["runtime_wiring_allowed"])

    def test_write_review_writes_only_under_done(self):
        result = _run_consumer(RESULT_RECORD, "--write-review")
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(DONE_REVIEW.exists())
        self.assertEqual(payload["review_status"], "pass")

    def test_original_result_and_ready_task_not_deleted(self):
        _run_consumer(RESULT_RECORD, "--write-review")
        self.assertTrue(RESULT_RECORD.exists())
        self.assertTrue(READY_TASK.exists())

    def test_no_dispatcher_run_codex_runtime_imports_or_network(self):
        source = CONSUMER.read_text(encoding="utf-8").lower()
        self.assertNotIn("import dispatcher", source)
        self.assertNotIn("from dispatcher", source)
        self.assertNotIn("import run_codex", source)
        self.assertNotIn("from run_codex", source)
        self.assertNotIn("runtime loop", source)
        self.assertNotIn("requests", source)
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("socket", source)

    def test_standard_library_only(self):
        source = CONSUMER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "sys", "datetime", "pathlib"})


if __name__ == "__main__":
    unittest.main()
