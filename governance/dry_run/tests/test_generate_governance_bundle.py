import ast
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "governance" / "dry_run" / "generate_governance_bundle.py"
FIXTURE = ROOT / "governance" / "fixtures" / "source_ai_orchestrator_result_stub.v1.json"
EXPECTED = ROOT / "governance" / "dry_run" / "expected_pm_v1_governance_bundle.v1.json"
VALIDATOR = ROOT / "governance" / "validation" / "validate_governance_artifacts.py"
FREEZE_REFERENCE = ROOT / "state" / "pm_v1_stable_warning_accepted_20260425.json"
ACTIVE_TASKS_DIR = ROOT / "active_tasks"
FORBIDDEN_IMPORT_FRAGMENTS = ("dispatcher", "run_codex", "runtime_loop")
EXPECTED_WARNINGS = {
    "network_risk": "mixed",
    "api_risk": "mixed",
    "wallet_risk": "mixed",
    "private_key_risk": "mixed",
    "execution_risk": "mixed",
    "live_trading_risk": "mixed",
    "dependency_risk": "docs_only",
}


def _run_generator(*extra_args):
    command = [sys.executable, str(GENERATOR), str(FIXTURE), *extra_args]
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)


class GenerateGovernanceBundleTests(unittest.TestCase):
    def test_generator_creates_expected_bundle_from_fixture(self):
        result = _run_generator()
        generated = json.loads(result.stdout)
        expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
        self.assertEqual(generated, expected)

    def test_generated_bundle_validates_with_existing_offline_validator(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(EXPECTED)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "valid")
        self.assertTrue(payload["warnings_preserved"])
        self.assertTrue(payload["final_done_allowed"])
        self.assertTrue(payload["single_runtime_source_rule_preserved"])

    def test_accepted_warnings_are_preserved_exactly(self):
        generated = json.loads(_run_generator().stdout)
        self.assertEqual(generated["adapter_envelope"]["accepted_warnings"], EXPECTED_WARNINGS)
        self.assertEqual(generated["critic_input_draft"]["accepted_warnings"], EXPECTED_WARNINGS)
        self.assertEqual(generated["governance_decision_record"]["accepted_warnings"], EXPECTED_WARNINGS)

    def test_source_run_id_consistency_is_preserved(self):
        generated = json.loads(_run_generator().stdout)
        source_run_id = generated["source_run_id"]
        self.assertEqual(generated["adapter_envelope"]["source_run_id"], source_run_id)
        self.assertEqual(generated["lifecycle_event_draft"]["source_run_id"], source_run_id)
        self.assertEqual(generated["critic_input_draft"]["source_run_id"], source_run_id)
        self.assertEqual(generated["governance_decision_record"]["source_run_id"], source_run_id)

    def test_task_id_consistency_is_preserved(self):
        generated = json.loads(_run_generator().stdout)
        task_id = generated["task_id"]
        self.assertEqual(generated["adapter_envelope"]["task_id"], task_id)
        self.assertEqual(generated["lifecycle_event_draft"]["task_id"], task_id)
        self.assertEqual(generated["critic_input_draft"]["task_id"], task_id)
        self.assertEqual(generated["governance_decision_record"]["task_id"], task_id)

    def test_final_done_without_critic_is_impossible(self):
        module = __import__("governance.dry_run.generate_governance_bundle", fromlist=["_build_bundle"])
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        invalid_cases = [
            {"critic_verdict": "warning", "governance_decision": "continue_review", "final_status_allowed": True},
            {"critic_verdict": "pass", "governance_decision": "accept_with_warnings", "final_status_allowed": True},
            {"critic_verdict": "warning", "governance_decision": "accept_with_warnings", "final_status_allowed": False},
            {"critic_verdict": "fail", "governance_decision": "accept_with_warnings", "final_status_allowed": True},
        ]
        for patch in invalid_cases:
            case = copy.deepcopy(fixture)
            case.update(patch)
            bundle = module._build_bundle(case)
            self.assertNotEqual(bundle["final_governance_status"], "done")

    def test_generator_imports_no_dispatcher(self):
        source = GENERATOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertFalse(any("dispatcher" in item for item in imports))

    def test_generator_imports_no_run_codex(self):
        source = GENERATOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertFalse(any("run_codex" in item for item in imports))

    def test_generator_imports_no_runtime_loop_modules(self):
        source = GENERATOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertFalse(any(fragment in item for item in imports for fragment in FORBIDDEN_IMPORT_FRAGMENTS))

    def test_generator_does_not_read_active_tasks(self):
        source = GENERATOR.read_text(encoding="utf-8")
        self.assertNotIn("active_tasks", source)
        self.assertFalse(ACTIVE_TASKS_DIR.exists() and "active_tasks" in str(FIXTURE))

    def test_generator_does_not_mutate_freeze_result_or_checkpoint_files(self):
        before = FREEZE_REFERENCE.read_bytes()
        _run_generator()
        after = FREEZE_REFERENCE.read_bytes()
        self.assertEqual(before, after)

    def test_generator_uses_python_standard_library_only(self):
        source = GENERATOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
        allowed = {"argparse", "json", "pathlib", "typing"}
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, allowed)


if __name__ == "__main__":
    unittest.main()
