import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from codex_auto.autopilot.prompt_packs.render_prompt_pack import (  # noqa: E402
    build_render_report_from_request_path,
    load_report_schema,
    load_request_schema,
    validate_output_path,
    validate_render_report,
    validate_render_request,
    write_render_report,
)

AUTOPILOT_ROOT = ROOT / "codex_auto" / "autopilot"
PROMPT_PACK_ROOT = AUTOPILOT_ROOT / "prompt_packs"
FIXTURES = PROMPT_PACK_ROOT / "fixtures"
OUTPUT_DIR = AUTOPILOT_ROOT / "tests" / "output"
CLI = PROMPT_PACK_ROOT / "render_prompt_pack.py"
PRECHECK_PATHS = [
    AUTOPILOT_ROOT / "classify_prompt_route.py",
    AUTOPILOT_ROOT / "run_routing_preflight.py",
]


def _load_json_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _run_cli(*args):
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class PromptPackRendererTests(unittest.TestCase):
    def test_request_schema_loads(self):
        schema = load_request_schema()
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0")

    def test_report_schema_loads(self):
        schema = load_report_schema()
        self.assertEqual(schema["properties"]["type"]["const"], "AUTOPILOT_PROMPT_PACK_RENDER_REPORT")

    def test_renderer_creates_deterministic_report_for_codex_code_changing_request(self):
        built = build_render_report_from_request_path(
            "codex_auto/autopilot/prompt_packs/fixtures/render_request_codex_code_changing.v1.json"
        )
        self.assertEqual(built, _load_json_fixture("expected_render_report_codex_code_changing.v1.json"))

    def test_rendered_codex_code_changing_prompt_includes_full_routing_header(self):
        report = build_render_report_from_request_path(
            "codex_auto/autopilot/prompt_packs/fixtures/render_request_codex_code_changing.v1.json"
        )
        routing_header = report["routing_header"]
        for field in [
            "TARGET_AGENT",
            "TASK_OWNER",
            "TASK_TYPE",
            "CODE_CHANGES_ALLOWED_FOR_RECEIVER",
            "SESSIONS_SPAWN_ALLOWED",
            "RUNTIME_MUTATION_ALLOWED",
            "QUEUE_MUTATION_ALLOWED",
            "GOVERNANCE_MUTATION_ALLOWED",
            "APPROVAL_REQUIRED",
            "MISROUTE_BEHAVIOR",
        ]:
            self.assertIn(field, routing_header)

    def test_rendered_codex_code_changing_prompt_checked_against_flocky_returns_misroute(self):
        report = build_render_report_from_request_path(
            "codex_auto/autopilot/prompt_packs/fixtures/render_request_codex_code_changing.v1.json"
        )
        self.assertEqual(report["preflight_report"]["required_behavior"], "MISROUTED_CODEX_PROMPT_DETECTED")

    def test_rendered_codex_repair_prompt_checked_against_flocky_returns_misroute(self):
        report = build_render_report_from_request_path(
            "codex_auto/autopilot/prompt_packs/fixtures/render_request_codex_repair.v1.json"
        )
        self.assertEqual(report["preflight_report"]["required_behavior"], "MISROUTED_CODEX_PROMPT_DETECTED")

    def test_rendered_flocky_validation_prompt_checked_against_flocky_returns_proceed_validation(self):
        report = build_render_report_from_request_path(
            "codex_auto/autopilot/prompt_packs/fixtures/render_request_flocky_validation.v1.json"
        )
        self.assertEqual(report, _load_json_fixture("expected_render_report_flocky_validation.v1.json"))

    def test_rendered_flocky_governance_prompt_checked_against_flocky_returns_proceed_governance(self):
        report = build_render_report_from_request_path(
            "codex_auto/autopilot/prompt_packs/fixtures/render_request_flocky_governance.v1.json"
        )
        self.assertEqual(report["preflight_report"]["required_behavior"], "PROCEED_GOVERNANCE_DESIGN")

    def test_rendered_chatgpt_planning_prompt_checked_against_flocky_returns_non_executable_behavior(self):
        report = build_render_report_from_request_path(
            "codex_auto/autopilot/prompt_packs/fixtures/render_request_chatgpt_planning.v1.json"
        )
        self.assertEqual(report["preflight_report"]["required_behavior"], "RETURN_ROUTING_MISMATCH")
        self.assertFalse(report["preflight_report"]["preflight_passed"])

    def test_unknown_template_request_fails(self):
        validation = validate_render_request(_load_json_fixture("invalid_render_request_unknown_template.v1.json"))
        self.assertFalse(validation["valid"])
        self.assertIn("unknown_template_name", validation["errors"])

    def test_target_template_mismatch_fails(self):
        validation = validate_render_request(_load_json_fixture("invalid_render_request_target_mismatch.v1.json"))
        self.assertFalse(validation["valid"])
        self.assertIn("target_agent_template_mismatch", validation["errors"])

    def test_final_acceptance_claim_fails(self):
        validation = validate_render_request(_load_json_fixture("invalid_render_request_final_acceptance_claim.v1.json"))
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden_claim:final_accepted", validation["errors"])

    def test_runtime_wiring_allowed_claim_fails(self):
        validation = validate_render_request(_load_json_fixture("invalid_render_request_runtime_wiring_allowed.v1.json"))
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden_claim:runtime_wiring_allowed", validation["errors"])

    def test_forbidden_output_paths_are_rejected(self):
        result = _run_cli(
            "--request-path",
            "codex_auto/autopilot/prompt_packs/fixtures/render_request_codex_code_changing.v1.json",
            "--out",
            "tasks/render_report.json",
        )
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertIn("output_path_forbidden:tasks/render_report.json", payload["errors"][0])

    def test_safe_output_paths_are_allowed(self):
        output_path = OUTPUT_DIR / "prompt_pack_render_report.json"
        if output_path.exists():
            output_path.unlink()
        result = _run_cli(
            "--request-path",
            "codex_auto/autopilot/prompt_packs/fixtures/render_request_flocky_validation.v1.json",
            "--out",
            "codex_auto/autopilot/tests/output/prompt_pack_render_report.json",
        )
        self.assertEqual(result.returncode, 0)
        self.assertTrue(output_path.exists())

    def test_no_files_written_by_default(self):
        output_path = OUTPUT_DIR / "prompt_pack_render_report_should_not_exist.json"
        if output_path.exists():
            output_path.unlink()
        result = _run_cli(
            "--request-path",
            "codex_auto/autopilot/prompt_packs/fixtures/render_request_codex_code_changing.v1.json",
            "--out",
            "-",
        )
        self.assertEqual(result.returncode, 0)
        self.assertFalse(output_path.exists())

    def test_rendered_prompt_does_not_contain_forbidden_active_permissions(self):
        report = build_render_report_from_request_path(
            "codex_auto/autopilot/prompt_packs/fixtures/render_request_codex_code_changing.v1.json"
        )
        prompt = report["rendered_prompt"]
        for term in [
            "EXECUTE_NOW",
            "FINAL_ACCEPTED",
            "RUNTIME_DONE",
            "AUTO_APPROVE_EXECUTION",
            "AUTO_APPLY_RUNTIME_STATE",
        ]:
            self.assertNotIn(term, prompt)

    def test_rendered_prompt_does_not_grant_sessions_spawn_to_flocky(self):
        report = build_render_report_from_request_path(
            "codex_auto/autopilot/prompt_packs/fixtures/render_request_codex_code_changing.v1.json"
        )
        prompt = report["rendered_prompt"]
        self.assertNotIn("SESSIONS_SPAWN_ALLOWED: true", prompt)
        self.assertNotIn("SESSIONS_SPAWN_ALLOWED_FOR_FLOCKY: true", prompt)

    def test_rendered_prompt_does_not_treat_codex_auto_as_runtime_source_of_truth(self):
        report = build_render_report_from_request_path(
            "codex_auto/autopilot/prompt_packs/fixtures/render_request_codex_code_changing.v1.json"
        )
        lowered = report["rendered_prompt"].lower()
        self.assertNotIn("source_of_truth=codex_auto", lowered)
        self.assertNotIn("authoritative_runtime_owner=codex_auto", lowered)

    def test_existing_classifier_preflight_files_are_unmodified_in_place(self):
        for path in PRECHECK_PATHS:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn("def main", text)
                self.assertIn("deterministic", text.lower())

    def test_report_validation_passes_for_expected_fixtures(self):
        for fixture_name in [
            "expected_render_report_codex_code_changing.v1.json",
            "expected_render_report_flocky_validation.v1.json",
        ]:
            with self.subTest(fixture=fixture_name):
                validation = validate_render_report(_load_json_fixture(fixture_name))
                self.assertTrue(validation["valid"])
                self.assertEqual(validation["errors"], [])

    def test_output_path_validator_rejects_non_render_area(self):
        with self.assertRaisesRegex(ValueError, "output_path_not_in_allowed_render_area"):
            validate_output_path("docs/render_report.json")

    def test_write_render_report_persists_json(self):
        output_path = OUTPUT_DIR / "prompt_pack_render_written_by_library.json"
        if output_path.exists():
            output_path.unlink()
        destination = write_render_report(
            "codex_auto/autopilot/tests/output/prompt_pack_render_written_by_library.json",
            _load_json_fixture("expected_render_report_flocky_validation.v1.json"),
        )
        self.assertEqual(destination, output_path)
        written = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(written["generated_by"], "codex_auto/autopilot/prompt_packs/render_prompt_pack.py")


if __name__ == "__main__":
    unittest.main()
