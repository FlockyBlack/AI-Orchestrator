import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
VALIDATOR = ROOT / "codex_auto" / "external_cli" / "one_shot" / "validate_one_shot_execution_gate.py"
GATE_PATH = ROOT / "codex_auto" / "external_cli" / "one_shot" / "PMBOT-BATCH-001.one_shot_execution_gate.json"
FINAL_PREVIEW_PATH = ROOT / "codex_auto" / "external_cli" / "one_shot" / "PMBOT-BATCH-001.final_command_preview.txt"


def run_validator(path: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ValidateOneShotExecutionGateTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        if not GATE_PATH.exists():
            raise AssertionError("missing gate fixture: " + str(GATE_PATH))
        if not FINAL_PREVIEW_PATH.exists():
            raise AssertionError("missing final preview fixture: " + str(FINAL_PREVIEW_PATH))
        cls.valid_gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))

    def write_temp_gate(self, tmpdir: Path, mutator):
        data = copy.deepcopy(self.valid_gate)
        mutator(data)
        path = tmpdir / "gate.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def assert_invalid(self, mutator, expected_fragment, preview_text=None):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            tmpdir = Path(temp_dir)
            if preview_text is not None:
                preview_path = tmpdir / "preview.txt"
                preview_path.write_text(preview_text, encoding="utf-8")

                def with_preview(data):
                    mutator(data)
                    data["final_command_preview_path"] = str(preview_path.relative_to(ROOT)).replace("\\", "/")

                path = self.write_temp_gate(tmpdir, with_preview)
            else:
                path = self.write_temp_gate(tmpdir, mutator)
            result = run_validator(path)
            payload = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
            serialized = json.dumps(payload)
            self.assertIn(expected_fragment, serialized)

    def test_gate_validates(self):
        result = run_validator(GATE_PATH)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(payload["status"], "valid")

    def test_final_preview_uses_non_interactive_editable_codex_command(self):
        preview = FINAL_PREVIEW_PATH.read_text(encoding="utf-8")
        self.assertIn("--full-auto", preview)
        self.assertIn("--skip-git-repo-check", preview)
        self.assertIn("MANUAL_RUN_ONLY", preview)
        self.assertIn("DO_NOT_EXECUTE_FROM_THIS_SCRIPT", preview)

    def test_validator_rejects_execution_allowed_now_true(self):
        self.assert_invalid(lambda data: data.__setitem__("execution_allowed_now", True), "execution_allowed_now_must_be_false")

    def test_validator_rejects_external_codex_cli_allowed_now_true(self):
        self.assert_invalid(lambda data: data.__setitem__("external_codex_cli_allowed_now", True), "external_codex_cli_allowed_now_must_be_false")

    def test_validator_rejects_generated_prompt_execution_allowed_now_true(self):
        self.assert_invalid(lambda data: data.__setitem__("generated_prompt_execution_allowed_now", True), "generated_prompt_execution_allowed_now_must_be_false")

    def test_validator_rejects_runtime_wiring_allowed_true(self):
        self.assert_invalid(lambda data: data.__setitem__("runtime_wiring_allowed", True), "runtime_wiring_allowed_must_be_false")

    def test_validator_rejects_missing_post_execution_flocky_validation_required(self):
        self.assert_invalid(lambda data: data.pop("post_execution_flocky_validation_required"), "missing:post_execution_flocky_validation_required")

    def test_validator_rejects_wallet_api_trading_live_api_real_order_terms(self):
        self.assert_invalid(
            lambda data: data.__setitem__("rollback_plan", "contains wallet api key private key trading live api real order authorization"),
            "forbidden_term:api_key",
        )

    def test_validator_rejects_final_done_claim(self):
        self.assert_invalid(lambda data: data.__setitem__("rollback_plan", "final Flocky/OpenClaw done"), "forbidden_term:final_done_claim")

    def test_validator_rejects_second_runtime_source_claim(self):
        self.assert_invalid(lambda data: data.__setitem__("rollback_plan", "second runtime source of truth"), "forbidden_term:second_runtime_source")

    def test_validator_rejects_missing_manual_run_only_marker(self):
        preview = FINAL_PREVIEW_PATH.read_text(encoding="utf-8").replace("MANUAL_RUN_ONLY\n", "", 1)
        self.assert_invalid(lambda data: None, "missing_preview_marker:manual_run_only", preview_text=preview)

    def test_validator_rejects_missing_full_auto_flag(self):
        preview = FINAL_PREVIEW_PATH.read_text(encoding="utf-8").replace("--full-auto ", "", 1)
        self.assert_invalid(lambda data: None, "final_command_preview_missing_full_auto", preview_text=preview)

    def test_validator_rejects_missing_skip_git_repo_check_flag(self):
        preview = FINAL_PREVIEW_PATH.read_text(encoding="utf-8").replace("--skip-git-repo-check ", "", 1)
        self.assert_invalid(lambda data: None, "final_command_preview_missing_skip_git_repo_check", preview_text=preview)

    def test_validator_standard_library_only_and_no_runtime_imports(self):
        tree = ast.parse(VALIDATOR.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertLessEqual(imported, {"json", "sys", "pathlib"})
        self.assertTrue(imported.isdisjoint({"dispatcher", "run_codex", "runtime", "state", "results", "freeze", "checkpoint"}))

    def test_validator_does_not_execute_external_codex_cli(self):
        source = VALIDATOR.read_text(encoding="utf-8").lower()
        self.assertNotIn("subprocess", source)
        self.assertNotIn("os.system", source)
        self.assertNotIn("popen", source)


if __name__ == "__main__":
    unittest.main()
