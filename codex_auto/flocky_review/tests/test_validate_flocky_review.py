import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "codex_auto" / "flocky_review" / "validate_flocky_review.py"
REVIEW_RECORD = ROOT / "codex_auto" / "tasks" / "done" / "FLOCKY-REVIEW-QUEUE-CODEX-AUTO-TINY-001.review.json"


def _run_validator(path: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ValidateFlockyReviewTests(unittest.TestCase):
    def setUp(self):
        REVIEW_RECORD.parent.mkdir(parents=True, exist_ok=True)
        self.valid_review = {
            "schema_version": "v1",
            "review_id": "FLOCKY-REVIEW-QUEUE-CODEX-AUTO-TINY-001",
            "queue_task_id": "QUEUE-CODEX-AUTO-TINY-001",
            "codex_task_id": "CODEX-AUTO-TINY-001",
            "reviewed_at": "2026-04-25T14:00:00+00:00",
            "reviewed_by": "flocky_local_review",
            "source_result_path": "codex_auto/tasks/needs_flocky_review/QUEUE-CODEX-AUTO-TINY-001.result.json",
            "source_queue_state": "needs_flocky_review",
            "review_status": "pass",
            "validation_findings": {},
            "safety_check": {
                "runtime_changed": False,
                "dispatcher_touched": False,
                "run_codex_touched": False,
                "active_task_files_touched": False,
                "freeze_record_modified": False,
                "result_records_modified": False,
                "checkpoint_records_modified": False,
                "network_used": False,
                "api_used": False,
                "wallet_used": False,
                "private_key_used": False,
                "trading_used": False,
                "external_codex_cli_invoked": False,
                "single_runtime_source_rule_preserved": True
            },
            "allowed_next_queue_state": "done",
            "final_flocky_done_claimed": False,
            "runtime_wiring_allowed": False,
            "notes": []
        }

    def _write(self, name: str, payload):
        path = REVIEW_RECORD.parent / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        self.addCleanup(lambda: path.unlink(missing_ok=True))
        return path

    def test_valid_review_record_passes(self):
        path = self._write("tmp_valid.review.json", self.valid_review)
        result = _run_validator(path)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "valid")

    def test_final_flocky_done_claimed_true_fails(self):
        payload = dict(self.valid_review)
        payload["final_flocky_done_claimed"] = True
        path = self._write("tmp_final_done.review.json", payload)
        out = json.loads(_run_validator(path).stdout)
        self.assertIn("final_flocky_done_claimed_must_be_false", out["errors"])

    def test_runtime_wiring_allowed_true_fails(self):
        payload = dict(self.valid_review)
        payload["runtime_wiring_allowed"] = True
        path = self._write("tmp_runtime_wiring.review.json", payload)
        out = json.loads(_run_validator(path).stdout)
        self.assertIn("runtime_wiring_allowed_must_be_false", out["errors"])

    def test_safety_flag_true_fails(self):
        payload = json.loads(json.dumps(self.valid_review))
        payload["safety_check"]["network_used"] = True
        path = self._write("tmp_bad_safety.review.json", payload)
        out = json.loads(_run_validator(path).stdout)
        self.assertIn("safety_check_network_used_must_be_false", out["errors"])

    def test_missing_required_fields_fail(self):
        payload = {"schema_version": "v1"}
        path = self._write("tmp_missing.review.json", payload)
        out = json.loads(_run_validator(path).stdout)
        self.assertIn("missing:review_id", out["errors"])

    def test_forbidden_wording_claiming_runtime_truth_fails(self):
        payload = json.loads(json.dumps(self.valid_review))
        payload["notes"] = ["This becomes runtime truth"]
        path = self._write("tmp_runtime_truth.review.json", payload)
        out = json.loads(_run_validator(path).stdout)
        self.assertIn("forbidden_term:runtime_truth", out["errors"])

    def test_standard_library_only(self):
        source = VALIDATOR.read_text(encoding="utf-8")
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
