import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "codex_auto" / "runner" / "run_codex_task.py"
APPROVED_FIXTURE = ROOT / "codex_auto" / "fixtures" / "approved_tiny_fixture_task.v1.json"
SAFE_FIXTURE = ROOT / "codex_auto" / "fixtures" / "safe_codex_task_fixture.v1.json"
OUTPUT_PATH = ROOT / "codex_auto" / "runs" / "CODEX-AUTO-TINY-001" / "fixture_output.json"
EXPECTED_PAYLOAD = {
    "schema_version": "v1",
    "task_id": "CODEX-AUTO-TINY-001",
    "artifact_type": "controlled_tiny_fixture_output",
    "created_by": "codex_auto_runner",
    "execution_mode": "controlled_tiny_sandbox",
    "runtime_wiring_added": False,
    "execution_allowed_beyond_fixture": False,
    "network_used": False,
    "api_used": False,
    "wallet_used": False,
    "private_key_used": False,
    "trading_used": False,
    "single_runtime_source_rule_preserved": True,
}


def _run_runner(*args):
    return subprocess.run(
        [sys.executable, str(RUNNER), *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ControlledTinyExecutionTests(unittest.TestCase):
    def setUp(self):
        self._original_output = None
        if OUTPUT_PATH.exists():
            self._original_output = OUTPUT_PATH.read_text(encoding="utf-8")
        OUTPUT_PATH.unlink(missing_ok=True)

    def tearDown(self):
        if self._original_output is None:
            OUTPUT_PATH.unlink(missing_ok=True)
        else:
            OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT_PATH.write_text(self._original_output, encoding="utf-8")

    def test_default_dry_run_does_not_create_fixture_output(self):
        result = _run_runner(SAFE_FIXTURE)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "dry_run_ready")
        self.assertFalse(OUTPUT_PATH.exists())

    def test_execute_without_valid_approval_remains_blocked(self):
        result = _run_runner(SAFE_FIXTURE, "--execute")
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["would_execute"])
        self.assertFalse(OUTPUT_PATH.exists())

    def test_execute_for_code_auto_tiny_with_valid_approval_creates_exact_fixture_output(self):
        result = _run_runner(APPROVED_FIXTURE, "--execute")
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["schema_version"], "codex_execution_envelope.v1")
        self.assertEqual(payload["execution_mode"], "controlled_tiny_sandbox")
        self.assertEqual(payload["result_status"], "completed")
        self.assertEqual(payload["files_created"], ["codex_auto/runs/CODEX-AUTO-TINY-001/fixture_output.json"])
        self.assertEqual(payload["files_modified_existing"], [])
        self.assertTrue(payload["openclaw_validation_required"])
        self.assertTrue(OUTPUT_PATH.exists())
        self.assertEqual(json.loads(OUTPUT_PATH.read_text(encoding="utf-8")), EXPECTED_PAYLOAD)
        created_files = [item.relative_to(OUTPUT_PATH.parent).as_posix() for item in OUTPUT_PATH.parent.glob("*") if item.is_file()]
        self.assertEqual(created_files, ["fixture_output.json"])

    def test_controlled_execution_envelope_does_not_claim_final_openclaw_done(self):
        result = _run_runner(APPROVED_FIXTURE, "--execute")
        payload = json.loads(result.stdout)
        serialized = json.dumps(payload).lower()
        self.assertNotIn("final openclaw done", serialized)
        self.assertNotIn("runtime source of truth", serialized)

    def test_safety_flags_remain_false_except_runtime_rule(self):
        result = _run_runner(APPROVED_FIXTURE, "--execute")
        payload = json.loads(result.stdout)
        safety = payload["safety_check"]
        self.assertFalse(safety["runtime_changed"])
        self.assertFalse(safety["dispatcher_touched"])
        self.assertFalse(safety["run_codex_touched"])
        self.assertFalse(safety["active_task_files_touched"])
        self.assertFalse(safety["freeze_record_modified"])
        self.assertFalse(safety["result_records_modified"])
        self.assertFalse(safety["checkpoint_records_modified"])
        self.assertFalse(safety["network_used"])
        self.assertFalse(safety["api_used"])
        self.assertFalse(safety["wallet_used"])
        self.assertFalse(safety["private_key_used"])
        self.assertFalse(safety["trading_used"])
        self.assertTrue(safety["single_runtime_source_rule_preserved"])

    def test_rerun_with_identical_existing_output_is_idempotent(self):
        first = _run_runner(APPROVED_FIXTURE, "--execute")
        first_payload = json.loads(first.stdout)
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first_payload["result_status"], "completed")

        second = _run_runner(APPROVED_FIXTURE, "--execute")
        second_payload = json.loads(second.stdout)
        self.assertEqual(second.returncode, 0)
        self.assertEqual(second_payload["result_status"], "completed")
        self.assertEqual(second_payload["files_created"], [])
        self.assertIn("already_exists_valid", second_payload["notes"])
        self.assertEqual(json.loads(OUTPUT_PATH.read_text(encoding="utf-8")), EXPECTED_PAYLOAD)

    def test_existing_unexpected_output_content_blocks(self):
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text("{\"unexpected\":true}\n", encoding="utf-8")
        result = _run_runner(APPROVED_FIXTURE, "--execute")
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["result_status"], "blocked")
        self.assertIn("existing_fixture_output_content_mismatch", payload["risks"])


if __name__ == "__main__":
    unittest.main()
