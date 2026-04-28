import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from codex_auto.autopilot.build_preview_handoff import (  # noqa: E402
    build_preview_handoff,
    load_schema,
    validate_output_path,
    validate_preview_handoff,
    write_preview_handoff,
)

AUTOPILOT_ROOT = ROOT / "codex_auto" / "autopilot"
FIXTURES = AUTOPILOT_ROOT / "fixtures"
OUTPUT_DIR = AUTOPILOT_ROOT / "tests" / "output"
CLI = AUTOPILOT_ROOT / "build_preview_handoff.py"


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


class BuildPreviewHandoffTests(unittest.TestCase):
    def test_library_build_matches_expected_fixture(self):
        built = build_preview_handoff(
            task_path="codex_auto/autopilot/fixtures/valid_runtime_task.json",
            run_path="codex_auto/autopilot/fixtures/valid_runtime_result.json",
            source_task_id="ORCH-AUTOPILOT-SAMPLE",
        )
        self.assertEqual(built, _load_fixture("expected_preview_handoff.v1.json"))

    def test_schema_file_loads_and_matches_version(self):
        schema = load_schema()
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            "autopilot_preview_handoff.v1",
        )

    def test_cli_defaults_to_stdout(self):
        result = _run_cli()
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["preview_only"])
        self.assertFalse(payload["execution_allowed_now"])

    def test_cli_can_write_inside_allowed_output_directory(self):
        output_path = OUTPUT_DIR / "preview_handoff.json"
        if output_path.exists():
            output_path.unlink()
        result = _run_cli("--out", "codex_auto/autopilot/tests/output/preview_handoff.json")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(output_path.exists())
        written = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(written["source_task_id"], "ORCH-AUTOPILOT-SAMPLE")

    def test_cli_rejects_forbidden_output_path(self):
        result = _run_cli("--out", "tasks/preview_handoff.json")
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertIn("output_path_forbidden:tasks/preview_handoff.json", payload["errors"])

    def test_output_path_validator_rejects_non_preview_area(self):
        with self.assertRaisesRegex(ValueError, "output_path_not_in_allowed_preview_area"):
            validate_output_path("docs/preview_handoff.json")

    def test_write_preview_handoff_persists_json(self):
        output_path = OUTPUT_DIR / "written_by_library.json"
        if output_path.exists():
            output_path.unlink()
        written = write_preview_handoff(
            "codex_auto/autopilot/tests/output/written_by_library.json",
            _load_fixture("expected_preview_handoff.v1.json"),
        )
        self.assertEqual(written, output_path)
        self.assertEqual(
            json.loads(output_path.read_text(encoding="utf-8"))["generated_by"],
            "codex_auto.autopilot.build_preview_handoff",
        )

    def test_invalid_fixtures_fail_validation(self):
        invalid_fixtures = {
            "invalid_runtime_authority_true.v1.json": "runtime_authority_must_be_false",
            "invalid_final_acceptance_authority_true.v1.json": "final_acceptance_authority_must_be_false",
            "invalid_execution_allowed_now_true.v1.json": "execution_allowed_now_must_be_false",
            "invalid_runtime_wiring_allowed_true.v1.json": "runtime_wiring_allowed_must_be_false",
            "invalid_missing_forbidden_paths.v1.json": "missing_forbidden_path:tasks/",
            "invalid_missing_flocky_validation_required.v1.json": "missing:flocky_validation_required",
            "invalid_source_of_truth_transfer_claim.v1.json": "forbidden_claim:source_of_truth_transfer",
        }
        for fixture_name, expected_error in invalid_fixtures.items():
            with self.subTest(fixture=fixture_name):
                with self.assertRaisesRegex(ValueError, expected_error):
                    validate_preview_handoff(_load_fixture(fixture_name))

    def test_preview_only_false_is_rejected(self):
        payload = _load_fixture("expected_preview_handoff.v1.json")
        payload["preview_only"] = False
        with self.assertRaisesRegex(ValueError, "preview_only_must_be_true"):
            validate_preview_handoff(payload)

    def test_source_task_id_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "source_task_id_mismatch:task"):
            build_preview_handoff(
                task_path="codex_auto/autopilot/fixtures/valid_runtime_task.json",
                run_path="codex_auto/autopilot/fixtures/valid_runtime_result.json",
                source_task_id="DIFFERENT-TASK-ID",
            )


if __name__ == "__main__":
    unittest.main()
