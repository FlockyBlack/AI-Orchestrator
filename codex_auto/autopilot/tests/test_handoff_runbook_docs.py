import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNBOOK_ROOT = ROOT / "codex_auto" / "autopilot" / "prompt_packs" / "runbooks"
CHECKLISTS = RUNBOOK_ROOT / "checklists"
EXAMPLES = RUNBOOK_ROOT / "examples"
MAIN_RUNBOOK = ROOT / "docs" / "AUTOPILOT_V1_RENDERED_PROMPT_HANDOFF_RUNBOOK.md"
QUICKSTART = RUNBOOK_ROOT / "OPERATOR_QUICKSTART.md"
RESULT_JSON = ROOT / "docs" / "ORCH_AUTOPILOT_015_RESULT.json"

CHECKLIST_FILES = [
    CHECKLISTS / "render_request_review_checklist.md",
    CHECKLISTS / "render_report_review_checklist.md",
    CHECKLISTS / "pre_send_checklist.md",
    CHECKLISTS / "post_result_checklist.md",
    CHECKLISTS / "misroute_incident_checklist.md",
]

EXAMPLE_FILES = [
    EXAMPLES / "example_codex_handoff_flow.md",
    EXAMPLES / "example_flocky_validation_flow.md",
    EXAMPLES / "example_repair_loop_flow.md",
    EXAMPLES / "example_misroute_incident_flow.md",
]

REQUIRED_RUNBOOK_SECTIONS = [
    "## Purpose",
    "## Current-stage boundaries",
    "## Manual handoff flow",
    "## Template selection rules",
    "## Render request review checklist",
    "## Render report review checklist",
    "## Preflight interpretation rules",
    "## Send/no-send decision rules",
    "## Result copy-back rules",
    "## Flocky validation requirement after Codex output",
    "## Repair loop rules",
    "## Misroute handling",
    "## Incident containment trigger",
    "## Acceptance rules",
    "## What remains manual",
    "## What is not implemented",
]

QUICKSTART_REQUIRED_STEPS = [
    "Choose the template",
    "Create the render request",
    "Run the renderer",
    "Inspect preflight",
    "Send the rendered prompt",
    "Copy the resulting agent output back",
    "Require Flocky read-only validation after any Codex output",
    "Stop on misroute",
]

FORBIDDEN_POSITIVE_CLAIMS = [
    "active_flocky_tool_integration=true",
    "runtime_wiring_allowed=true",
    "queue_bridge_active=true",
    "dispatcher_integration_active=true",
    "run_codex_integration_active=true",
    "source_of_truth=codex_auto",
    "authoritative_runtime_owner=codex_auto",
    "EXECUTE_NOW",
    "FINAL_ACCEPTED",
    "RUNTIME_DONE",
    "AUTO_APPROVE_EXECUTION",
    "AUTO_APPLY_RUNTIME_STATE",
]

DISALLOWED_REAL_PATH_SNIPPETS = [
    "C:\\Users\\OpenC\\Documents\\AI-Orchestrator",
    "C:/Users/OpenC/Documents/AI-Orchestrator",
    "tasks/",
    "runs/",
    "state/",
    "runtime/",
    "results/",
    "freeze/",
    "checkpoint/",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class HandoffRunbookDocsTests(unittest.TestCase):
    def test_all_expected_files_exist(self):
        expected = [MAIN_RUNBOOK, QUICKSTART, RESULT_JSON, *CHECKLIST_FILES, *EXAMPLE_FILES]
        for path in expected:
            with self.subTest(path=path.name):
                self.assertTrue(path.exists(), str(path))

    def test_main_runbook_includes_required_sections(self):
        text = _read(MAIN_RUNBOOK)
        for section in REQUIRED_RUNBOOK_SECTIONS:
            with self.subTest(section=section):
                self.assertIn(section, text)

    def test_quickstart_includes_required_flow_steps(self):
        text = _read(QUICKSTART)
        for step in QUICKSTART_REQUIRED_STEPS:
            with self.subTest(step=step):
                self.assertIn(step, text)

    def test_checklists_include_stop_conditions(self):
        for path in CHECKLIST_FILES:
            text = _read(path)
            with self.subTest(path=path.name):
                self.assertIn("Stop if", text)

    def test_examples_use_placeholder_ids_and_paths_only(self):
        placeholder_task_pattern = re.compile(r"<TASK_ID_[A-Z_]+>")
        placeholder_path_pattern = re.compile(r"<PROJECT_ROOT>/")
        for path in EXAMPLE_FILES:
            text = _read(path)
            with self.subTest(path=path.name):
                self.assertRegex(text, placeholder_task_pattern)
                self.assertRegex(text, placeholder_path_pattern)
                for disallowed in DISALLOWED_REAL_PATH_SNIPPETS:
                    self.assertNotIn(disallowed, text)

    def test_docs_do_not_claim_active_or_runtime_behavior(self):
        docs = [MAIN_RUNBOOK, QUICKSTART, *CHECKLIST_FILES, *EXAMPLE_FILES]
        combined = "\n".join(_read(path) for path in docs)
        for claim in FORBIDDEN_POSITIVE_CLAIMS:
            with self.subTest(claim=claim):
                self.assertNotIn(claim, combined)

    def test_docs_do_not_claim_queue_bridge_dispatcher_or_run_codex_integration(self):
        combined = "\n".join(_read(path) for path in [MAIN_RUNBOOK, QUICKSTART, *CHECKLIST_FILES, *EXAMPLE_FILES]).lower()
        self.assertNotIn("queue bridge is active", combined)
        self.assertNotIn("dispatcher integration is active", combined)
        self.assertNotIn("run_codex integration is active", combined)

    def test_docs_do_not_claim_final_acceptance_execution_approval_or_runtime_done(self):
        combined = "\n".join(_read(path) for path in [MAIN_RUNBOOK, QUICKSTART, *CHECKLIST_FILES, *EXAMPLE_FILES]).lower()
        self.assertNotIn("final acceptance authority is granted", combined)
        self.assertNotIn("execution approval is granted", combined)
        self.assertNotIn("runtime done is confirmed", combined)

    def test_docs_do_not_treat_codex_auto_as_runtime_source_of_truth(self):
        combined = "\n".join(_read(path) for path in [MAIN_RUNBOOK, QUICKSTART, *CHECKLIST_FILES, *EXAMPLE_FILES]).lower()
        self.assertNotIn("codex_auto source of truth", combined)
        self.assertNotIn("codex_auto runtime authority", combined)

    def test_docs_mention_flocky_validation_requirement_after_codex_output(self):
        combined = "\n".join(_read(path) for path in [MAIN_RUNBOOK, QUICKSTART, *CHECKLIST_FILES, *EXAMPLE_FILES])
        self.assertIn("Flocky read-only validation after any Codex output", combined)

    def test_docs_mention_misroute_containment_if_wrong_agent_execution_occurs(self):
        text = _read(MAIN_RUNBOOK)
        self.assertIn("If wrong-agent execution occurs, treat it as an incident and move to containment immediately.", text)
        self.assertIn("Trigger containment if a wrong agent executes a prompt.", text)

    def test_docs_mention_renderer_does_not_execute_or_send_prompts(self):
        combined = "\n".join(_read(path) for path in [MAIN_RUNBOOK, QUICKSTART, *CHECKLIST_FILES])
        self.assertIn("does not execute or send prompts", combined)

    def test_result_json_has_required_shape_and_safety_flags(self):
        payload = json.loads(_read(RESULT_JSON))
        self.assertEqual(payload["task_id"], "ORCH-AUTOPILOT-015-HANDOFF-RUNBOOK-DOCS")
        self.assertIn(payload["status"], ["implementation_complete_ready_for_flocky_validation", "blocked"])
        self.assertTrue(payload["handoff_runbook_docs"]["created"])
        self.assertTrue(payload["handoff_runbook_docs"]["main_runbook_created"])
        self.assertTrue(payload["handoff_runbook_docs"]["quickstart_created"])
        self.assertFalse(payload["handoff_runbook_docs"]["active_flocky_tool_integration"])
        self.assertFalse(payload["handoff_runbook_docs"]["runtime_wiring_allowed"])
        self.assertFalse(payload["handoff_runbook_docs"]["queue_bridge_allowed"])
        self.assertTrue(payload["safety"]["single_runtime_source_rule_preserved"])
        for key in [
            "runtime_wiring",
            "dispatcher_changed",
            "run_codex_changed",
            "active_task_mutation",
            "state_result_freeze_checkpoint_mutation",
            "codex_auto_queue_mutation",
            "governance_mutation",
            "flocky_tool_integration",
            "sessions_spawn",
            "external_codex_execution",
            "generated_prompt_execution",
            "rendered_prompt_execution",
            "prompt_sending",
            "network_api",
            "credentials",
            "wallet_private_key",
            "orders_trading",
            "final_acceptance_claimed",
            "execution_approval_claimed",
        ]:
            with self.subTest(flag=key):
                self.assertFalse(payload["safety"][key])


if __name__ == "__main__":
    unittest.main()
