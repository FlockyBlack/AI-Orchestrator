import ast
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
APPROVAL_PATH = ROOT / "codex_auto" / "external_cli" / "approval" / "PMBOT-BATCH-001.approval_request.json"
VALIDATOR_PATH = ROOT / "codex_auto" / "external_cli" / "approval" / "validate_external_execution_approval.py"


def run_validator(path):
    target = path if path.is_absolute() else (ROOT / path)
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(target)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


class ExternalExecutionApprovalValidationTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.valid_data = json.loads(APPROVAL_PATH.read_text(encoding="utf-8"))

    def write_temp_request(self, tmp_path, mutator):
        data = copy.deepcopy(self.valid_data)
        mutator(data)
        target = tmp_path / "approval_request.json"
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return target

    def assert_invalid(self, mutator, expected_fragment):
        with self.subTest(expected_fragment=expected_fragment):
            from tempfile import TemporaryDirectory

            with TemporaryDirectory() as tmpdir:
                temp_path = self.write_temp_request(Path(tmpdir), mutator)
                code, stdout, _ = run_validator(temp_path)
                self.assertNotEqual(code, 0)
                self.assertIn(expected_fragment, stdout)

    def test_valid_pending_request_passes(self):
        code, stdout, stderr = run_validator(APPROVAL_PATH)
        self.assertEqual(code, 0, msg=stderr)
        payload = json.loads(stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["approval_status"], "pending_human_approval")
        self.assertFalse(payload["execution_allowed_now"])
        self.assertFalse(payload["external_codex_cli_allowed_now"])
        self.assertFalse(payload["generated_prompt_execution_allowed_now"])
        self.assertFalse(payload["runtime_wiring_allowed"])

    def test_pending_with_execution_allowed_now_true_fails(self):
        self.assert_invalid(lambda data: data.__setitem__("execution_allowed_now", True), "pending_human_approval cannot set execution_allowed_now=true")

    def test_pending_with_external_codex_cli_allowed_now_true_fails(self):
        self.assert_invalid(lambda data: data.__setitem__("external_codex_cli_allowed_now", True), "pending_human_approval cannot set external_codex_cli_allowed_now=true")

    def test_pending_with_generated_prompt_execution_allowed_now_true_fails(self):
        self.assert_invalid(lambda data: data.__setitem__("generated_prompt_execution_allowed_now", True), "pending_human_approval cannot set generated_prompt_execution_allowed_now=true")

    def test_runtime_wiring_allowed_true_fails(self):
        self.assert_invalid(lambda data: data.__setitem__("runtime_wiring_allowed", True), "runtime_wiring_allowed must be false")

    def test_missing_prompt_path_fails(self):
        self.assert_invalid(lambda data: data.__setitem__("approved_prompt_path", "codex_auto/prompts/DOES-NOT-EXIST.txt"), "approved prompt path does not exist")

    def test_missing_command_preview_path_fails(self):
        self.assert_invalid(lambda data: data.__setitem__("approved_command_preview_path", "codex_auto/external_cli/plans/DOES-NOT-EXIST.txt"), "approved command preview path does not exist")

    def test_allowed_output_path_escape_fails(self):
        def mutate(data):
            data["allowed_output_paths"] = list(data["allowed_output_paths"])
            data["allowed_output_paths"][0] = "../pm_bot/paper/"

        self.assert_invalid(mutate, "allowed_output_paths must exactly match the approved list")

    def test_missing_protected_forbidden_paths_fail(self):
        def mutate(data):
            data["forbidden_paths"] = [path for path in data["forbidden_paths"] if path not in {"scripts/dispatcher.py", "scripts/run_codex.py", "runtime/", "state/"}]

        self.assert_invalid(mutate, "forbidden_paths missing protected surfaces")

    def test_missing_rollback_plan_fails(self):
        self.assert_invalid(lambda data: data.__setitem__("rollback_plan", ""), "rollback_plan must be present")

    def test_missing_post_execution_flocky_validation_required_fails(self):
        self.assert_invalid(lambda data: data.pop("post_execution_flocky_validation_required"), "missing required fields: post_execution_flocky_validation_required")

    def test_wallet_private_key_trading_live_api_real_orders_indicators_fail(self):
        def mutate(data):
            data["approval_reason"] = "wallet private key trading live Polymarket real orders"

        self.assert_invalid(mutate, "approval request contains banned content")

    def test_final_done_claim_fails(self):
        self.assert_invalid(lambda data: data.__setitem__("approval_reason", "final Flocky/OpenClaw done"), "approval request contains banned content: final flocky/openclaw done")

    def test_second_runtime_source_claim_fails(self):
        self.assert_invalid(lambda data: data.__setitem__("approval_reason", "second runtime source of truth"), "approval request contains banned content: second runtime source")

    def test_validator_imports_no_dispatcher_run_codex_runtime_modules(self):
        tree = ast.parse(VALIDATOR_PATH.read_text(encoding="utf-8"))
        forbidden = {"dispatcher", "run_codex", "runtime", "state", "results", "freeze", "checkpoint"}
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertTrue(imported.isdisjoint(forbidden), msg=f"forbidden imports found: {imported & forbidden}")

    def test_validator_does_not_execute_external_codex_cli(self):
        source = VALIDATOR_PATH.read_text(encoding="utf-8").lower()
        self.assertNotIn("subprocess", source)
        self.assertNotIn("codex exec", source)
        self.assertNotIn("os.system", source)
        self.assertNotIn("popen", source)


if __name__ == "__main__":
    unittest.main()
