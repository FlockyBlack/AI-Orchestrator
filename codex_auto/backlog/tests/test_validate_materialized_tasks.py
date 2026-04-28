import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "codex_auto" / "backlog" / "validate_materialized_tasks.py"
CANDIDATES = [
    ROOT / "codex_auto" / "tasks" / "candidates" / "PMBOT-005-PAPER-SIMULATION.task.json",
    ROOT / "codex_auto" / "tasks" / "candidates" / "PMBOT-006-RISK-LIMITS.task.json",
    ROOT / "codex_auto" / "tasks" / "candidates" / "PMBOT-007-FEES-SLIPPAGE.task.json",
    ROOT / "codex_auto" / "tasks" / "candidates" / "PMBOT-008-RESEARCH-DASHBOARD.task.json",
    ROOT / "codex_auto" / "tasks" / "candidates" / "PMBOT-009-FIXTURE-POSTMORTEM.task.json",
    ROOT / "codex_auto" / "tasks" / "candidates" / "PMBOT-010-STATIC-SAFETY-AUDIT.task.json",
]


def _run_validator(path: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ValidateMaterializedTasksTests(unittest.TestCase):
    def test_all_generated_candidates_validate(self):
        for candidate in CANDIDATES:
            result = _run_validator(candidate)
            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(payload["status"], "valid")

    def test_missing_required_field_fails(self):
        payload = json.loads(CANDIDATES[0].read_text(encoding="utf-8"))
        payload.pop("generated_prompt_ref")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            out = json.loads(_run_validator(path).stdout)
            self.assertIn("missing:generated_prompt_ref", out["errors"])

    def test_approved_for_execution_true_fails(self):
        payload = json.loads(CANDIDATES[0].read_text(encoding="utf-8"))
        payload["approved_for_execution"] = True
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "approved.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            out = json.loads(_run_validator(path).stdout)
            self.assertIn("approved_for_execution_must_be_false", out["errors"])

    def test_queue_state_ready_fails(self):
        payload = json.loads(CANDIDATES[0].read_text(encoding="utf-8"))
        payload["queue_state"] = "ready"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ready.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            out = json.loads(_run_validator(path).stdout)
            self.assertIn("queue_state_must_be_candidate", out["errors"])

    def test_runtime_wiring_allowed_true_fails(self):
        payload = json.loads(CANDIDATES[0].read_text(encoding="utf-8"))
        payload["runtime_wiring_allowed"] = True
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "runtime.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            out = json.loads(_run_validator(path).stdout)
            self.assertIn("runtime_wiring_allowed_must_be_false", out["errors"])

    def test_external_codex_cli_allowed_true_fails(self):
        payload = json.loads(CANDIDATES[0].read_text(encoding="utf-8"))
        payload["external_codex_cli_allowed"] = True
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "cli.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            out = json.loads(_run_validator(path).stdout)
            self.assertIn("external_codex_cli_allowed_must_be_false", out["errors"])

    def test_missing_forbidden_path_fails(self):
        payload = json.loads(CANDIDATES[0].read_text(encoding="utf-8"))
        payload["forbidden_paths"] = ["runtime/", "freeze/", "checkpoint/"]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "paths.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            out = json.loads(_run_validator(path).stdout)
            self.assertIn("missing_forbidden_path:scripts/dispatcher.py", out["errors"])
            self.assertIn("missing_forbidden_path:scripts/run_codex.py", out["errors"])

    def test_forbidden_scope_terms_fail(self):
        payload = json.loads(CANDIDATES[0].read_text(encoding="utf-8"))
        payload["forbidden_scope"] = ["dispatcher modification"]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "scope.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            out = json.loads(_run_validator(path).stdout)
            self.assertIn("missing_forbidden_scope:network", out["errors"])
            self.assertIn("missing_forbidden_scope:api", out["errors"])
            self.assertIn("missing_forbidden_scope:wallet", out["errors"])

    def test_final_done_claim_fails(self):
        payload = json.loads(CANDIDATES[0].read_text(encoding="utf-8"))
        payload["forbidden_scope"].append("allow final Flocky done")
        payload["notes"] = ["final Flocky done"]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "done.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            out = json.loads(_run_validator(path).stdout)
            self.assertIn("forbidden_final_done_claim", out["errors"])

    def test_second_runtime_truth_claim_fails(self):
        payload = json.loads(CANDIDATES[0].read_text(encoding="utf-8"))
        payload["summary"] = "This becomes runtime truth."
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "truth.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            out = json.loads(_run_validator(path).stdout)
            self.assertIn("forbidden_runtime_truth_claim", out["errors"])


if __name__ == "__main__":
    unittest.main()
