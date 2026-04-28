import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from codex_auto.autopilot.run_routing_preflight import build_routing_preflight_report_from_path  # noqa: E402

AUTOPILOT_ROOT = ROOT / "codex_auto" / "autopilot"
PROMPT_PACK_ROOT = AUTOPILOT_ROOT / "prompt_packs"
TEMPLATES_DIR = PROMPT_PACK_ROOT / "templates"
EXAMPLES_DIR = PROMPT_PACK_ROOT / "examples"
MANIFEST_PATH = PROMPT_PACK_ROOT / "prompt_pack_manifest.v1.json"

REQUIRED_HEADERS = [
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
]
TEMPLATE_FILES = [
    "flocky_read_only_validation.template.txt",
    "flocky_governance_design.template.txt",
    "codex_code_changing.template.txt",
    "codex_focused_repair.template.txt",
    "chatgpt_planning.template.txt",
]
EXAMPLE_FILES = [
    "example_flocky_validation_prompt.txt",
    "example_flocky_governance_prompt.txt",
    "example_codex_code_changing_prompt.txt",
    "example_codex_repair_prompt.txt",
    "example_chatgpt_planning_prompt.txt",
]
FORBIDDEN_CLAIMS = [
    "EXECUTE_NOW",
    "FINAL_ACCEPTED",
    "RUNTIME_DONE",
    "AUTO_APPROVE_EXECUTION",
    "AUTO_APPLY_RUNTIME_STATE",
    "source_of_truth=codex_auto",
    "authoritative_runtime_owner=codex_auto",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _header_map(text: str):
    result = {}
    for raw_line in text.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        if key.strip() in REQUIRED_HEADERS or key.strip() == "SESSIONS_SPAWN_ALLOWED_FOR_FLOCKY":
            result[key.strip()] = value.strip()
    return result


class PromptPackTemplateTests(unittest.TestCase):
    def test_every_template_exists(self):
        for filename in TEMPLATE_FILES:
            with self.subTest(template=filename):
                self.assertTrue((TEMPLATES_DIR / filename).exists())

    def test_every_template_has_required_routing_header_fields(self):
        for filename in TEMPLATE_FILES:
            with self.subTest(template=filename):
                headers = _header_map(_read(TEMPLATES_DIR / filename))
                for field in REQUIRED_HEADERS:
                    self.assertIn(field, headers)

    def test_flocky_templates_have_all_restricted_flags_false(self):
        for filename in [
            "flocky_read_only_validation.template.txt",
            "flocky_governance_design.template.txt",
        ]:
            with self.subTest(template=filename):
                headers = _header_map(_read(TEMPLATES_DIR / filename))
                self.assertEqual(headers["TARGET_AGENT"], "Flocky")
                self.assertEqual(headers["TASK_OWNER"], "Flocky")
                self.assertEqual(headers["CODE_CHANGES_ALLOWED_FOR_RECEIVER"], "false")
                self.assertEqual(headers["SESSIONS_SPAWN_ALLOWED"], "false")
                self.assertEqual(headers["RUNTIME_MUTATION_ALLOWED"], "false")
                self.assertEqual(headers["QUEUE_MUTATION_ALLOWED"], "false")
                self.assertEqual(headers["GOVERNANCE_MUTATION_ALLOWED"], "false")

    def test_codex_templates_include_flocky_misroute_behavior(self):
        for filename in [
            "codex_code_changing.template.txt",
            "codex_focused_repair.template.txt",
        ]:
            with self.subTest(template=filename):
                text = _read(TEMPLATES_DIR / filename)
                headers = _header_map(text)
                self.assertEqual(headers["TARGET_AGENT"], "Codex")
                self.assertIn("MISROUTED_CODEX_PROMPT_DETECTED", headers["MISROUTE_BEHAVIOR"])
                self.assertEqual(headers["SESSIONS_SPAWN_ALLOWED"], "false")
                self.assertEqual(headers["SESSIONS_SPAWN_ALLOWED_FOR_FLOCKY"], "false")

    def test_chatgpt_planning_template_has_no_execution_or_mutation_authority(self):
        headers = _header_map(_read(TEMPLATES_DIR / "chatgpt_planning.template.txt"))
        self.assertEqual(headers["TARGET_AGENT"], "ChatGPT")
        self.assertEqual(headers["TASK_TYPE"], "planning")
        self.assertEqual(headers["CODE_CHANGES_ALLOWED_FOR_RECEIVER"], "false")
        self.assertEqual(headers["SESSIONS_SPAWN_ALLOWED"], "false")
        self.assertEqual(headers["RUNTIME_MUTATION_ALLOWED"], "false")
        self.assertEqual(headers["QUEUE_MUTATION_ALLOWED"], "false")
        self.assertEqual(headers["GOVERNANCE_MUTATION_ALLOWED"], "false")

    def test_manifest_references_all_templates(self):
        manifest = json.loads(_read(MANIFEST_PATH))
        listed = {item["template_name"] for item in manifest["prompt_pack_templates"]}
        self.assertEqual(listed, set(TEMPLATE_FILES))

    def test_examples_exist(self):
        for filename in EXAMPLE_FILES:
            with self.subTest(example=filename):
                self.assertTrue((EXAMPLES_DIR / filename).exists())

    def test_examples_include_headers(self):
        for filename in EXAMPLE_FILES:
            with self.subTest(example=filename):
                headers = _header_map(_read(EXAMPLES_DIR / filename))
                for field in REQUIRED_HEADERS:
                    self.assertIn(field, headers)

    def test_codex_code_changing_template_received_by_flocky_is_misrouted(self):
        report = build_routing_preflight_report_from_path(
            "Flocky",
            "codex_auto/autopilot/prompt_packs/templates/codex_code_changing.template.txt",
        )
        self.assertEqual(report["required_behavior"], "MISROUTED_CODEX_PROMPT_DETECTED")
        self.assertFalse(report["preflight_passed"])

    def test_codex_repair_template_received_by_flocky_is_misrouted(self):
        report = build_routing_preflight_report_from_path(
            "Flocky",
            "codex_auto/autopilot/prompt_packs/templates/codex_focused_repair.template.txt",
        )
        self.assertEqual(report["required_behavior"], "MISROUTED_CODEX_PROMPT_DETECTED")
        self.assertFalse(report["preflight_passed"])

    def test_flocky_validation_template_received_by_flocky_proceeds_validation(self):
        report = build_routing_preflight_report_from_path(
            "Flocky",
            "codex_auto/autopilot/prompt_packs/templates/flocky_read_only_validation.template.txt",
        )
        self.assertEqual(report["required_behavior"], "PROCEED_READ_ONLY_VALIDATION")
        self.assertTrue(report["preflight_passed"])

    def test_flocky_governance_template_received_by_flocky_proceeds_governance(self):
        report = build_routing_preflight_report_from_path(
            "Flocky",
            "codex_auto/autopilot/prompt_packs/templates/flocky_governance_design.template.txt",
        )
        self.assertEqual(report["required_behavior"], "PROCEED_GOVERNANCE_DESIGN")
        self.assertTrue(report["preflight_passed"])

    def test_chatgpt_planning_template_received_by_flocky_returns_non_executable_behavior(self):
        report = build_routing_preflight_report_from_path(
            "Flocky",
            "codex_auto/autopilot/prompt_packs/templates/chatgpt_planning.template.txt",
        )
        self.assertFalse(report["preflight_passed"])
        self.assertEqual(report["required_behavior"], "RETURN_ROUTING_MISMATCH")

    def test_no_template_contains_forbidden_execution_approval_claims(self):
        for filename in TEMPLATE_FILES:
            with self.subTest(template=filename):
                text = _read(TEMPLATES_DIR / filename)
                for claim in FORBIDDEN_CLAIMS:
                    self.assertNotIn(claim, text)

    def test_no_template_grants_sessions_spawn_to_flocky(self):
        for filename in TEMPLATE_FILES:
            with self.subTest(template=filename):
                text = _read(TEMPLATES_DIR / filename)
                self.assertNotIn("SESSIONS_SPAWN_ALLOWED: true", text)
                self.assertNotIn("SESSIONS_SPAWN_ALLOWED_FOR_FLOCKY: true", text)

    def test_no_template_grants_runtime_queue_or_governance_mutation(self):
        for filename in TEMPLATE_FILES:
            with self.subTest(template=filename):
                headers = _header_map(_read(TEMPLATES_DIR / filename))
                self.assertEqual(headers["RUNTIME_MUTATION_ALLOWED"], "false")
                self.assertEqual(headers["QUEUE_MUTATION_ALLOWED"], "false")
                self.assertEqual(headers["GOVERNANCE_MUTATION_ALLOWED"], "false")

    def test_no_template_treats_codex_auto_as_runtime_source_of_truth(self):
        for filename in TEMPLATE_FILES:
            with self.subTest(template=filename):
                lowered = _read(TEMPLATES_DIR / filename).lower()
                self.assertNotIn("source_of_truth=codex_auto", lowered)
                self.assertNotIn("authoritative_runtime_owner=codex_auto", lowered)


if __name__ == "__main__":
    unittest.main()
