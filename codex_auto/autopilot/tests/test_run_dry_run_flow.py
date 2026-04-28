import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from codex_auto.autopilot.run_dry_run_flow import (  # noqa: E402
    build_dry_run_flow_report,
    load_schema,
    validate_dry_run_report,
    validate_output_path,
    write_dry_run_report,
)

AUTOPILOT_ROOT = ROOT / "codex_auto" / "autopilot"
FIXTURES = AUTOPILOT_ROOT / "fixtures"
OUTPUT_DIR = AUTOPILOT_ROOT / "tests" / "output"
CLI = AUTOPILOT_ROOT / "run_dry_run_flow.py"


def _load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _run_cli(*extra_args):
    return subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--task-path",
            "codex_auto/autopilot/fixtures/valid_runtime_task.json",
            "--run-path",
            "codex_auto/autopilot/fixtures/valid_runtime_result.json",
            "--source-task-id",
            "ORCH-AUTOPILOT-SAMPLE",
            *extra_args,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class RunDryRunFlowTests(unittest.TestCase):
    def test_library_build_matches_expected_fixture(self):
        built = build_dry_run_flow_report(
            task_path="codex_auto/autopilot/fixtures/valid_runtime_task.json",
            run_path="codex_auto/autopilot/fixtures/valid_runtime_result.json",
            source_task_id="ORCH-AUTOPILOT-SAMPLE",
        )
        self.assertEqual(built, _load_fixture("expected_dry_run_report.v1.json"))

    def test_schema_file_loads_and_matches_version(self):
        schema = load_schema()
        self.assertEqual(schema["properties"]["schema_version"]["const"], "autopilot_dry_run_report.v1")

    def test_cli_defaults_to_stdout(self):
        result = _run_cli()
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["dry_run_only"])
        self.assertFalse(payload["execution_allowed_now"])
        self.assertEqual(payload["next_action_recommendation"], "ready_for_flocky_review")

    def test_cli_can_write_inside_allowed_output_directory(self):
        output_path = OUTPUT_DIR / "dry_run_report.json"
        if output_path.exists():
            output_path.unlink()
        result = _run_cli("--out", "codex_auto/autopilot/tests/output/dry_run_report.json")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(output_path.exists())
        written = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(written["generated_by"], "codex_auto.autopilot.run_dry_run_flow")

    def test_cli_rejects_forbidden_output_path(self):
        result = _run_cli("--out", "tasks/dry_run_report.json")
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertIn("output_path_forbidden:tasks/dry_run_report.json", payload["errors"][0])

    def test_output_path_validator_rejects_non_dry_run_area(self):
        with self.assertRaisesRegex(ValueError, "output_path_not_in_allowed_dry_run_area"):
            validate_output_path("docs/dry_run_report.json")

    def test_write_dry_run_report_persists_json(self):
        output_path = OUTPUT_DIR / "dry_run_written_by_library.json"
        if output_path.exists():
            output_path.unlink()
        written = write_dry_run_report(
            "codex_auto/autopilot/tests/output/dry_run_written_by_library.json",
            _load_fixture("expected_dry_run_report.v1.json"),
        )
        self.assertEqual(written, output_path)
        self.assertEqual(
            json.loads(output_path.read_text(encoding="utf-8"))["generated_by"],
            "codex_auto.autopilot.run_dry_run_flow",
        )

    def test_expected_fixture_validates_with_non_blocking_fixture_warnings(self):
        report = validate_dry_run_report(_load_fixture("expected_dry_run_report.v1.json"))
        self.assertTrue(report["valid"])
        self.assertEqual(report["type"], "AUTOPILOT_DRY_RUN_FLOW_REPORT_VALIDATION")
        self.assertIn("example_reference_path:authoritative_task_path", report["warnings"])
        self.assertIn("example_reference_path:authoritative_run_path_or_ref", report["warnings"])
        self.assertEqual(report["errors"], [])

    def test_invalid_fixtures_fail_validation(self):
        invalid_fixtures = {
            "invalid_dry_run_runtime_authority_true.v1.json": "runtime_authority_must_be_false",
            "invalid_dry_run_final_acceptance_authority_true.v1.json": "final_acceptance_authority_must_be_false",
            "invalid_dry_run_execution_allowed_now_true.v1.json": "execution_allowed_now_must_be_false",
            "invalid_dry_run_runtime_wiring_allowed_true.v1.json": "runtime_wiring_allowed_must_be_false",
            "invalid_dry_run_queue_mutation_allowed_true.v1.json": "queue_mutation_allowed_must_be_false",
            "invalid_dry_run_final_acceptance_claimed_true.v1.json": "final_acceptance_claimed_must_be_false",
            "invalid_dry_run_bad_next_action_execute_now.v1.json": "next_action_recommendation_invalid",
            "invalid_dry_run_missing_forbidden_paths.v1.json": "missing_forbidden_path:tasks/",
            "invalid_dry_run_source_of_truth_transfer_claim.v1.json": "forbidden_claim:source_of_truth",
        }
        for fixture_name, expected_error in invalid_fixtures.items():
            with self.subTest(fixture=fixture_name):
                report = validate_dry_run_report(_load_fixture(fixture_name))
                self.assertFalse(report["valid"])
                self.assertIn(expected_error, report["errors"])

    def test_preview_contract_failure_recommends_repair(self):
        payload = _load_fixture("expected_dry_run_report.v1.json")
        payload["preview_handoff_ref_or_inline"]["runtime_authority"] = True
        report = validate_dry_run_report(payload)
        self.assertFalse(report["valid"])
        self.assertIn("preview_handoff_invalid:runtime_authority_must_be_false", report["errors"])

    def test_realistic_runtime_references_validate_without_fixture_warning(self):
        payload = _load_fixture("expected_dry_run_report.v1.json")
        task_ref = "tasks/ready/ORCH-AUTOPILOT-SAMPLE.task.json"
        run_ref = "runs/ORCH-AUTOPILOT-SAMPLE/20260426T000000Z/result.json"
        payload["authoritative_task_path"] = task_ref
        payload["authoritative_run_path_or_ref"] = run_ref
        payload["preview_handoff_ref_or_inline"]["authoritative_task_path"] = task_ref
        payload["preview_handoff_ref_or_inline"]["authoritative_run_path_or_ref"] = run_ref
        report = validate_dry_run_report(payload)
        self.assertTrue(report["valid"])
        self.assertEqual(report["warnings"], [])


if __name__ == "__main__":
    unittest.main()
