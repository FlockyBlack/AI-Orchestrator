import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from codex_auto.autopilot.classify_prompt_route import (  # noqa: E402
    classify_prompt_route,
    classify_prompt_route_path,
    load_schema,
)

AUTOPILOT_ROOT = ROOT / "codex_auto" / "autopilot"
FIXTURES = AUTOPILOT_ROOT / "fixtures"
CLI = AUTOPILOT_ROOT / "classify_prompt_route.py"


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


class ClassifyPromptRouteTests(unittest.TestCase):
    def test_schema_loads(self):
        schema = load_schema()
        self.assertEqual(schema["properties"]["type"]["const"], "AUTOPILOT_PROMPT_ROUTING_DECISION")

    def test_codex_code_changing_prompt_received_by_flocky_is_misrouted(self):
        decision = classify_prompt_route_path("Flocky", "codex_auto/autopilot/fixtures/prompt_codex_code_changing_task.txt")
        self.assertEqual(decision, _load_json_fixture("expected_route_codex_received_by_flocky.v1.json"))

    def test_codex_repair_prompt_received_by_flocky_is_misrouted(self):
        decision = classify_prompt_route_path("Flocky", "codex_auto/autopilot/fixtures/prompt_codex_repair_task.txt")
        self.assertEqual(decision["routing_class"], "CODEX_REPAIR_TASK")
        self.assertEqual(decision["required_behavior"], "MISROUTED_CODEX_PROMPT_DETECTED")
        self.assertIn("codex_task_received_by_flocky", decision["blocking_reasons"])

    def test_flocky_validation_prompt_received_by_flocky_proceeds_read_only(self):
        decision = classify_prompt_route_path("Flocky", "codex_auto/autopilot/fixtures/prompt_flocky_validation_task.txt")
        self.assertEqual(decision, _load_json_fixture("expected_route_flocky_validation_received_by_flocky.v1.json"))

    def test_flocky_governance_prompt_received_by_flocky_proceeds_governance_design(self):
        decision = classify_prompt_route_path("Flocky", "codex_auto/autopilot/fixtures/prompt_flocky_governance_task.txt")
        self.assertEqual(decision["routing_class"], "FLOCKY_GOVERNANCE_TASK")
        self.assertEqual(decision["required_behavior"], "PROCEED_GOVERNANCE_DESIGN")
        self.assertTrue(decision["safe_for_receiver_to_execute"])

    def test_mixed_owner_prompt_returns_routing_mismatch(self):
        decision = classify_prompt_route_path("Flocky", "codex_auto/autopilot/fixtures/prompt_ambiguous_mixed_owner_task.txt")
        self.assertEqual(decision, _load_json_fixture("expected_route_ambiguous_mixed_owner.v1.json"))

    def test_unsafe_sessions_spawn_prompt_is_blocked(self):
        decision = classify_prompt_route_path("Flocky", "codex_auto/autopilot/fixtures/prompt_unsafe_sessions_spawn_task.txt")
        self.assertEqual(decision, _load_json_fixture("expected_route_unsafe_sessions_spawn.v1.json"))

    def test_missing_header_with_strong_codex_signals_received_by_flocky_is_misrouted(self):
        decision = classify_prompt_route_path("Flocky", "codex_auto/autopilot/fixtures/prompt_missing_header_with_codex_signals.txt")
        self.assertEqual(decision["routing_class"], "CODEX_CODE_CHANGING_TASK")
        self.assertEqual(decision["required_behavior"], "MISROUTED_CODEX_PROMPT_DETECTED")
        self.assertIn("missing_header:TARGET_AGENT", decision["warnings"])

    def test_sessions_spawn_allowed_is_always_false_for_flocky(self):
        for fixture in [
            "prompt_codex_code_changing_task.txt",
            "prompt_flocky_validation_task.txt",
            "prompt_flocky_governance_task.txt",
            "prompt_ambiguous_mixed_owner_task.txt",
        ]:
            with self.subTest(fixture=fixture):
                decision = classify_prompt_route_path("Flocky", f"codex_auto/autopilot/fixtures/{fixture}")
                self.assertFalse(decision["sessions_spawn_allowed"])

    def test_code_changes_allowed_is_always_false_for_flocky(self):
        decision = classify_prompt_route_path("Flocky", "codex_auto/autopilot/fixtures/prompt_codex_code_changing_task.txt")
        self.assertFalse(decision["code_changes_allowed_for_receiver"])

    def test_mutation_flags_false_by_default_for_flocky(self):
        decision = classify_prompt_route_path("Flocky", "codex_auto/autopilot/fixtures/prompt_flocky_governance_task.txt")
        self.assertFalse(decision["runtime_mutation_allowed"])
        self.assertFalse(decision["queue_mutation_allowed"])
        self.assertFalse(decision["governance_mutation_allowed"])

    def test_detected_signals_include_expected_markers(self):
        decision = classify_prompt_route_path("Flocky", "codex_auto/autopilot/fixtures/prompt_codex_code_changing_task.txt")
        self.assertIn("codex_signal:задание codex", decision["detected_signals"])
        self.assertIn("codex_signal:run pytest", decision["detected_signals"])

    def test_output_is_deterministic(self):
        prompt_text = _load_text_fixture("prompt_codex_code_changing_task.txt")
        first = classify_prompt_route("Flocky", prompt_text)
        second = classify_prompt_route("Flocky", prompt_text)
        self.assertEqual(first, second)

    def test_cli_prompt_file_mode_works(self):
        result = _run_cli("--receiver", "Flocky", "--prompt-path", "codex_auto/autopilot/fixtures/prompt_codex_code_changing_task.txt")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["required_behavior"], "MISROUTED_CODEX_PROMPT_DETECTED")

    def test_cli_stdin_mode_works(self):
        prompt_text = _load_text_fixture("prompt_flocky_validation_task.txt")
        result = _run_cli("--receiver", "Flocky", "--prompt-path", "-", input_text=prompt_text)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["required_behavior"], "PROCEED_READ_ONLY_VALIDATION")

    def test_classifier_does_not_write_files_by_default(self):
        marker = AUTOPILOT_ROOT / "tests" / "output" / "classifier_should_not_create.json"
        if marker.exists():
            marker.unlink()
        result = _run_cli("--receiver", "Flocky", "--prompt-path", "codex_auto/autopilot/fixtures/prompt_codex_code_changing_task.txt")
        self.assertEqual(result.returncode, 0)
        self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
