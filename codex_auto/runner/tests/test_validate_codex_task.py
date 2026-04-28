import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "codex_auto" / "runner" / "validate_codex_task.py"
FIXTURES = ROOT / "codex_auto" / "fixtures"


def _run_validator(path: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ValidateCodexTaskTests(unittest.TestCase):
    def test_safe_fixture_validates(self):
        result = _run_validator(FIXTURES / "safe_codex_task_fixture.v1.json")
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "valid")
        self.assertFalse(payload["execution_allowed"])
        self.assertTrue(payload["dry_run_default"])

    def test_invalid_runtime_touch_fixture_fails(self):
        result = _run_validator(FIXTURES / "invalid_codex_task_forbidden_runtime_touch.v1.json")
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "invalid")
        self.assertTrue(any("dispatcher" in err or "runtime" in err for err in payload["errors"]))

    def test_invalid_network_wallet_trading_fixture_fails(self):
        result = _run_validator(FIXTURES / "invalid_codex_task_network_wallet_trading.v1.json")
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "invalid")
        self.assertIn("forbidden_term:network", payload["errors"])
        self.assertIn("forbidden_term:wallet", payload["errors"])
        self.assertIn("forbidden_term:trading", payload["errors"])

    def test_missing_required_fields_fail(self):
        fixture = ROOT / "codex_auto" / "runs" / "tmp_missing_required.json"
        fixture.write_text(json.dumps({"task_id": "TMP"}), encoding="utf-8")
        self.addCleanup(lambda: fixture.unlink(missing_ok=True))
        result = _run_validator(fixture)
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "invalid")
        self.assertIn("missing:schema_version", payload["errors"])

    def test_forbidden_allowed_paths_fail(self):
        base = json.loads((FIXTURES / "safe_codex_task_fixture.v1.json").read_text(encoding="utf-8"))
        base["allowed_paths"] = ["scripts/dispatcher.py"]
        fixture = ROOT / "codex_auto" / "runs" / "tmp_forbidden_allowed_path.json"
        fixture.write_text(json.dumps(base), encoding="utf-8")
        self.addCleanup(lambda: fixture.unlink(missing_ok=True))
        result = _run_validator(fixture)
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "invalid")
        self.assertIn("dispatcher_path_forbidden", payload["errors"])

    def test_approved_for_execution_true_fails_safe_default(self):
        base = json.loads((FIXTURES / "safe_codex_task_fixture.v1.json").read_text(encoding="utf-8"))
        base["approved_for_execution"] = True
        fixture = ROOT / "codex_auto" / "runs" / "tmp_approved_true.json"
        fixture.write_text(json.dumps(base), encoding="utf-8")
        self.addCleanup(lambda: fixture.unlink(missing_ok=True))
        result = _run_validator(fixture)
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("approved_for_execution_must_be_false_by_default", payload["errors"])

    def test_prompt_with_wallet_private_key_trading_live_api_fails(self):
        base = json.loads((FIXTURES / "safe_codex_task_fixture.v1.json").read_text(encoding="utf-8"))
        base["prompt"] = "Inspect a wallet private key and use the live Polymarket API for trading."
        fixture = ROOT / "codex_auto" / "runs" / "tmp_wallet_prompt.json"
        fixture.write_text(json.dumps(base), encoding="utf-8")
        self.addCleanup(lambda: fixture.unlink(missing_ok=True))
        result = _run_validator(fixture)
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("forbidden_term:wallet", payload["errors"])
        self.assertIn("forbidden_term:private_key", payload["errors"])
        self.assertIn("forbidden_term:trading", payload["errors"])
        self.assertIn("forbidden_term:api", payload["errors"])

    def test_prompt_with_dispatcher_run_codex_runtime_mutation_fails(self):
        base = json.loads((FIXTURES / "safe_codex_task_fixture.v1.json").read_text(encoding="utf-8"))
        base["prompt"] = "Modify dispatcher, run_codex, and the runtime loop, then mutate the active task."
        fixture = ROOT / "codex_auto" / "runs" / "tmp_runtime_prompt.json"
        fixture.write_text(json.dumps(base), encoding="utf-8")
        self.addCleanup(lambda: fixture.unlink(missing_ok=True))
        result = _run_validator(fixture)
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("forbidden_term:dispatcher", payload["errors"])
        self.assertIn("forbidden_term:run_codex", payload["errors"])

    def test_validator_standard_library_only(self):
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
