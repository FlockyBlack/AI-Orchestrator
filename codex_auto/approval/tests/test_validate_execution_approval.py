import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "codex_auto" / "approval" / "validate_execution_approval.py"
FIXTURES = ROOT / "codex_auto" / "fixtures"


def _run_validator(path: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ValidateExecutionApprovalTests(unittest.TestCase):
    def test_approved_tiny_fixture_validates(self):
        result = _run_validator(FIXTURES / "approved_tiny_fixture_task.v1.json")
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "valid")
        self.assertTrue(payload["execution_approved"])
        self.assertFalse(payload["runtime_wiring_allowed"])
        self.assertTrue(payload["openclaw_validation_required"])

    def test_invalid_missing_approval_metadata_fails(self):
        result = _run_validator(FIXTURES / "invalid_missing_approval_metadata.v1.json")
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "invalid")
        self.assertIn("approved_by_must_be_non_empty", payload["errors"])
        self.assertIn("expected_tests_must_be_non_empty_list", payload["errors"])

    def test_invalid_approval_forbidden_path_escape_fails(self):
        result = _run_validator(FIXTURES / "invalid_approval_forbidden_path_escape.v1.json")
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "invalid")
        self.assertTrue(any("allowed_path_outside_approved_sandbox" in err or "dispatcher_path_forbidden" in err for err in payload["errors"]))

    def test_invalid_approval_runtime_wiring_fails(self):
        result = _run_validator(FIXTURES / "invalid_approval_runtime_wiring.v1.json")
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "invalid")
        self.assertIn("forbidden_term:runtime_wiring", payload["errors"])
        self.assertIn("forbidden_term:dispatcher", payload["errors"])
        self.assertIn("forbidden_term:run_codex", payload["errors"])

    def test_validator_imports_no_dispatcher_or_run_codex_or_runtime_loop_modules(self):
        source = VALIDATOR.read_text(encoding="utf-8").lower()
        self.assertNotIn("import dispatcher", source)
        self.assertNotIn("from dispatcher", source)
        self.assertNotIn("import run_codex", source)
        self.assertNotIn("from run_codex", source)
        self.assertNotIn("runtime loop module", source)

    def test_validator_does_not_call_network_api_wallet_or_trading(self):
        source = VALIDATOR.read_text(encoding="utf-8").lower()
        self.assertNotIn("requests", source)
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("socket", source)

    def test_validator_does_not_mutate_files(self):
        source = VALIDATOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_calls = {"write_text", "write_bytes", "mkdir", "rename", "unlink", "rmdir"}
        seen = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute):
                    seen.add(func.attr)
        self.assertTrue(forbidden_calls.isdisjoint(seen))

    def test_standard_library_only(self):
        source = VALIDATOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
