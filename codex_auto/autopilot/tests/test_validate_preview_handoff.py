import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from codex_auto.autopilot.validate_preview_handoff import (  # noqa: E402
    validate_preview_handoff_data,
    validate_preview_handoff_file,
)

AUTOPILOT_ROOT = ROOT / "codex_auto" / "autopilot"
FIXTURES = AUTOPILOT_ROOT / "fixtures"
VALIDATOR = AUTOPILOT_ROOT / "validate_preview_handoff.py"
BUILDER = AUTOPILOT_ROOT / "build_preview_handoff.py"


def _load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _run_validator(*args, input_text=None):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        input=input_text,
        check=False,
    )


class ValidatePreviewHandoffTests(unittest.TestCase):
    def test_expected_preview_fixture_validates_with_non_blocking_fixture_warnings(self):
        report = validate_preview_handoff_file("codex_auto/autopilot/fixtures/expected_preview_handoff.v1.json")
        self.assertTrue(report["valid"])
        self.assertEqual(report["type"], "AUTOPILOT_PREVIEW_HANDOFF_VALIDATION_REPORT")
        self.assertIn("example_reference_path:authoritative_task_path", report["warnings"])
        self.assertIn("example_reference_path:authoritative_run_path_or_ref", report["warnings"])
        self.assertEqual(report["errors"], [])

    def test_validator_cli_validates_expected_fixture(self):
        result = _run_validator("--preview-path", "codex_auto/autopilot/fixtures/expected_preview_handoff.v1.json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertTrue(payload["preview_only"])
        self.assertFalse(payload["runtime_authority"])

    def test_builder_stdout_can_be_validated_from_stdin(self):
        built = subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                "--task-path",
                "codex_auto/autopilot/fixtures/valid_runtime_task.json",
                "--run-path",
                "codex_auto/autopilot/fixtures/valid_runtime_result.json",
                "--source-task-id",
                "ORCH-AUTOPILOT-SAMPLE",
                "--out",
                "-",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(built.returncode, 0)
        validated = _run_validator("--preview-path", "-", input_text=built.stdout)
        self.assertEqual(validated.returncode, 0)
        payload = json.loads(validated.stdout)
        self.assertTrue(payload["valid"])
        self.assertIn("example_reference_path:authoritative_task_path", payload["warnings"])

    def test_invalid_fixtures_fail(self):
        invalid_fixtures = {
            "invalid_runtime_authority_true.v1.json": "runtime_authority_must_be_false",
            "invalid_final_acceptance_authority_true.v1.json": "final_acceptance_authority_must_be_false",
            "invalid_execution_allowed_now_true.v1.json": "execution_allowed_now_must_be_false",
            "invalid_runtime_wiring_allowed_true.v1.json": "runtime_wiring_allowed_must_be_false",
            "invalid_missing_forbidden_paths.v1.json": "missing_forbidden_path:tasks/",
            "invalid_missing_flocky_validation_required.v1.json": "missing:flocky_validation_required",
            "invalid_source_of_truth_transfer_claim.v1.json": "forbidden_claim:source_of_truth_transfer",
            "invalid_codex_auto_runtime_owner.v1.json": "runtime_status_owner_must_be:AI-Orchestrator",
            "invalid_final_accepted_claim.v1.json": "forbidden_claim:final_accepted",
            "invalid_missing_status_ownership.v1.json": "missing:status_ownership",
            "invalid_missing_stop_conditions.v1.json": "missing:stop_conditions",
            "invalid_bad_authoritative_path_claim.v1.json": "bad_authoritative_path_claim:authoritative_task_path",
            "invalid_missing_approval_required.v1.json": "missing:approval_required",
        }
        for fixture_name, expected_error in invalid_fixtures.items():
            with self.subTest(fixture=fixture_name):
                report = validate_preview_handoff_data(_load_fixture(fixture_name))
                self.assertFalse(report["valid"])
                self.assertIn(expected_error, report["errors"])

    def test_final_acceptance_owner_drift_fails(self):
        payload = _load_fixture("expected_preview_handoff.v1.json")
        payload["status_ownership"]["final_acceptance_status"]["owner"] = "Flocky"
        report = validate_preview_handoff_data(payload)
        self.assertFalse(report["valid"])
        self.assertIn("final_acceptance_status_owner_must_be:AI-Orchestrator", report["errors"])
        self.assertIn("forbidden_claim:final_acceptance_owner_drift", report["errors"])

    def test_runtime_wiring_allowed_true_fails(self):
        payload = _load_fixture("expected_preview_handoff.v1.json")
        payload["runtime_wiring_allowed"] = True
        report = validate_preview_handoff_data(payload)
        self.assertFalse(report["valid"])
        self.assertIn("runtime_wiring_allowed_must_be_false", report["errors"])

    def test_execution_allowed_now_true_fails(self):
        payload = _load_fixture("expected_preview_handoff.v1.json")
        payload["execution_allowed_now"] = True
        report = validate_preview_handoff_data(payload)
        self.assertFalse(report["valid"])
        self.assertIn("execution_allowed_now_must_be_false", report["errors"])

    def test_runtime_truth_transfer_claim_fails(self):
        payload = _load_fixture("expected_preview_handoff.v1.json")
        payload["runtime_truth_transferred"] = True
        report = validate_preview_handoff_data(payload)
        self.assertFalse(report["valid"])
        self.assertIn("forbidden_claim:runtime_truth_transferred", report["errors"])

    def test_realistic_runtime_references_validate_without_fixture_warning(self):
        payload = _load_fixture("expected_preview_handoff.v1.json")
        payload["authoritative_task_path"] = "tasks/ready/ORCH-AUTOPILOT-SAMPLE.task.json"
        payload["authoritative_run_path_or_ref"] = "runs/ORCH-AUTOPILOT-SAMPLE/20260426T000000Z/result.json"
        report = validate_preview_handoff_data(payload)
        self.assertTrue(report["valid"])
        self.assertEqual(report["warnings"], [])


if __name__ == "__main__":
    unittest.main()
