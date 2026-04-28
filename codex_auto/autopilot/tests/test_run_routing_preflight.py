import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from codex_auto.autopilot.run_routing_preflight import (  # noqa: E402
    build_routing_preflight_report,
    build_routing_preflight_report_from_path,
    load_schema,
    validate_output_path,
    validate_preflight_report,
    write_preflight_report,
)

AUTOPILOT_ROOT = ROOT / "codex_auto" / "autopilot"
FIXTURES = AUTOPILOT_ROOT / "fixtures"
OUTPUT_DIR = AUTOPILOT_ROOT / "tests" / "output"
CLI = AUTOPILOT_ROOT / "run_routing_preflight.py"


def _load_json_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _load_text_fixture(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def _run_cli(*args, input_text=None):
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        input=input_text,
        check=False,
    )


class RunRoutingPreflightTests(unittest.TestCase):
    def test_schema_loads(self):
        schema = load_schema()
        self.assertEqual(schema["properties"]["type"]["const"], "AUTOPILOT_ROUTING_PREFLIGHT_REPORT")

    def test_codex_code_changing_prompt_received_by_flocky_is_blocked_as_misroute(self):
        report = build_routing_preflight_report_from_path("Flocky", "codex_auto/autopilot/fixtures/prompt_codex_code_changing_task.txt")
        self.assertEqual(report, _load_json_fixture("expected_preflight_codex_received_by_flocky.v1.json"))

    def test_codex_repair_prompt_received_by_flocky_is_blocked_as_misroute(self):
        report = build_routing_preflight_report_from_path("Flocky", "codex_auto/autopilot/fixtures/prompt_codex_repair_task.txt")
        self.assertFalse(report["preflight_passed"])
        self.assertFalse(report["safe_for_receiver_to_continue"])
        self.assertEqual(report["required_behavior"], "MISROUTED_CODEX_PROMPT_DETECTED")
        self.assertEqual(report["next_action"], "RESEND_TO_CODEX")

    def test_flocky_validation_prompt_received_by_flocky_proceeds_read_only(self):
        report = build_routing_preflight_report_from_path("Flocky", "codex_auto/autopilot/fixtures/prompt_flocky_validation_task.txt")
        self.assertEqual(report, _load_json_fixture("expected_preflight_flocky_validation_received_by_flocky.v1.json"))

    def test_flocky_governance_prompt_received_by_flocky_proceeds_governance_design(self):
        report = build_routing_preflight_report_from_path("Flocky", "codex_auto/autopilot/fixtures/prompt_flocky_governance_task.txt")
        self.assertEqual(report, _load_json_fixture("expected_preflight_flocky_governance_received_by_flocky.v1.json"))

    def test_ambiguous_mixed_owner_prompt_returns_routing_mismatch(self):
        report = build_routing_preflight_report_from_path("Flocky", "codex_auto/autopilot/fixtures/prompt_ambiguous_mixed_owner_task.txt")
        self.assertEqual(report, _load_json_fixture("expected_preflight_ambiguous_mixed_owner.v1.json"))

    def test_unsafe_sessions_spawn_prompt_is_blocked(self):
        report = build_routing_preflight_report_from_path("Flocky", "codex_auto/autopilot/fixtures/prompt_unsafe_sessions_spawn_task.txt")
        self.assertEqual(report, _load_json_fixture("expected_preflight_unsafe_sessions_spawn.v1.json"))

    def test_missing_header_with_codex_signals_returns_misroute_behavior(self):
        report = build_routing_preflight_report_from_path("Flocky", "codex_auto/autopilot/fixtures/prompt_missing_header_with_codex_signals.txt")
        self.assertFalse(report["preflight_passed"])
        self.assertEqual(report["required_behavior"], "MISROUTED_CODEX_PROMPT_DETECTED")
        self.assertIn("missing_header:TARGET_AGENT", report["warnings"])

    def test_library_build_from_text_is_deterministic(self):
        prompt_text = _load_text_fixture("prompt_codex_code_changing_task.txt")
        first = build_routing_preflight_report("Flocky", prompt_text, prompt_source="inline")
        second = build_routing_preflight_report("Flocky", prompt_text, prompt_source="inline")
        self.assertEqual(first, second)

    def test_expected_fixtures_validate(self):
        for fixture_name in [
            "expected_preflight_codex_received_by_flocky.v1.json",
            "expected_preflight_flocky_validation_received_by_flocky.v1.json",
            "expected_preflight_flocky_governance_received_by_flocky.v1.json",
            "expected_preflight_ambiguous_mixed_owner.v1.json",
            "expected_preflight_unsafe_sessions_spawn.v1.json",
        ]:
            with self.subTest(fixture=fixture_name):
                validation = validate_preflight_report(_load_json_fixture(fixture_name))
                self.assertTrue(validation["valid"])
                self.assertEqual(validation["errors"], [])

    def test_invalid_fixtures_fail_validation(self):
        invalid_fixtures = {
            "invalid_preflight_sessions_spawn_allowed_true.v1.json": "sessions_spawn_allowed_must_be_false",
            "invalid_preflight_original_prompt_executed_true.v1.json": "original_prompt_executed_must_be_false",
            "invalid_preflight_active_flocky_tool_integration_true.v1.json": "active_flocky_tool_integration_must_be_false",
            "invalid_preflight_runtime_wiring_allowed_true.v1.json": "runtime_wiring_allowed_must_be_false",
            "invalid_preflight_bad_next_action_execute_now.v1.json": "forbidden_next_action:EXECUTE_NOW",
            "invalid_preflight_source_of_truth_transfer_claim.v1.json": "forbidden_claim:source_of_truth",
        }
        for fixture_name, expected_error in invalid_fixtures.items():
            with self.subTest(fixture=fixture_name):
                validation = validate_preflight_report(_load_json_fixture(fixture_name))
                self.assertFalse(validation["valid"])
                self.assertIn(expected_error, validation["errors"])

    def test_direct_forbidden_claim_mutations_fail_validation(self):
        report = _load_json_fixture("expected_preflight_flocky_validation_received_by_flocky.v1.json")
        report["dispatcher_integration_allowed"] = True
        report["run_codex_integration_allowed"] = True
        validation = validate_preflight_report(report)
        self.assertFalse(validation["valid"])
        self.assertIn("dispatcher_integration_allowed_must_be_false", validation["errors"])
        self.assertIn("run_codex_integration_allowed_must_be_false", validation["errors"])

    def test_cli_prompt_file_mode_works(self):
        result = _run_cli(
            "--receiver",
            "Flocky",
            "--prompt-path",
            "codex_auto/autopilot/fixtures/prompt_codex_code_changing_task.txt",
            "--out",
            "-",
        )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["required_behavior"], "MISROUTED_CODEX_PROMPT_DETECTED")
        self.assertFalse(payload["preflight_passed"])

    def test_cli_stdin_mode_works(self):
        result = _run_cli(
            "--receiver",
            "Flocky",
            "--prompt-path",
            "-",
            "--out",
            "-",
            input_text=_load_text_fixture("prompt_flocky_validation_task.txt"),
        )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["prompt_source"], "stdin")
        self.assertEqual(payload["required_behavior"], "PROCEED_READ_ONLY_VALIDATION")

    def test_simulator_does_not_write_files_by_default(self):
        output_path = OUTPUT_DIR / "preflight_should_not_exist.json"
        if output_path.exists():
            output_path.unlink()
        result = _run_cli(
            "--receiver",
            "Flocky",
            "--prompt-path",
            "codex_auto/autopilot/fixtures/prompt_codex_code_changing_task.txt",
        )
        self.assertEqual(result.returncode, 0)
        self.assertFalse(output_path.exists())

    def test_forbidden_output_paths_are_rejected(self):
        result = _run_cli(
            "--receiver",
            "Flocky",
            "--prompt-path",
            "codex_auto/autopilot/fixtures/prompt_codex_code_changing_task.txt",
            "--out",
            "tasks/preflight.json",
        )
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertIn("output_path_forbidden:tasks/preflight.json", payload["errors"][0])

    def test_allowed_output_paths_are_written(self):
        output_path = OUTPUT_DIR / "routing_preflight_report.json"
        if output_path.exists():
            output_path.unlink()
        result = _run_cli(
            "--receiver",
            "Flocky",
            "--prompt-path",
            "codex_auto/autopilot/fixtures/prompt_flocky_validation_task.txt",
            "--out",
            "codex_auto/autopilot/tests/output/routing_preflight_report.json",
        )
        self.assertEqual(result.returncode, 0)
        self.assertTrue(output_path.exists())
        written = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(written["generated_by"], "codex_auto/autopilot/run_routing_preflight.py")

    def test_output_path_validator_rejects_non_preflight_area(self):
        with self.assertRaisesRegex(ValueError, "output_path_not_in_allowed_preflight_area"):
            validate_output_path("docs/preflight.json")

    def test_write_preflight_report_persists_json(self):
        output_path = OUTPUT_DIR / "routing_preflight_written_by_library.json"
        if output_path.exists():
            output_path.unlink()
        destination = write_preflight_report(
            "codex_auto/autopilot/tests/output/routing_preflight_written_by_library.json",
            _load_json_fixture("expected_preflight_flocky_validation_received_by_flocky.v1.json"),
        )
        self.assertEqual(destination, output_path)
        written = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(written["next_action"], "CONTINUE_READ_ONLY_VALIDATION")


if __name__ == "__main__":
    unittest.main()
