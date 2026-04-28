import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "codex_auto" / "external_cli" / "validate_external_codex_plan.py"
PLAN = ROOT / "codex_auto" / "external_cli" / "plans" / "PMBOT-BATCH-001.external_codex_plan.json"


def _run_validator(path: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ValidateExternalCodexPlanTests(unittest.TestCase):
    def test_plan_validates(self):
        result = _run_validator(PLAN)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "valid")

    def test_validator_rejects_plan_if_external_codex_cli_allowed_now_true(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "plan.json"
            payload = json.loads(PLAN.read_text(encoding="utf-8"))
            payload["external_codex_cli_allowed_now"] = True
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = _run_validator(path)
            data = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("external_codex_cli_allowed_now_must_be_false", data["errors"])

    def test_validator_rejects_runtime_wiring(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "plan.json"
            payload = json.loads(PLAN.read_text(encoding="utf-8"))
            payload["safety_check"]["runtime_wiring_allowed"] = True
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = _run_validator(path)
            data = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("runtime_wiring_allowed_must_be_false", data["errors"])

    def test_validator_rejects_secrets_api_wallet_private_key_trading_indicators(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "plan.json"
            payload = json.loads(PLAN.read_text(encoding="utf-8"))
            payload["command_preview"] += "\ncontains secret wallet private key trading live api"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = _run_validator(path)
            data = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("forbidden_term:secret", data["errors"])
            self.assertIn("forbidden_term:wallet", data["errors"])
            self.assertIn("forbidden_term:private_key", data["errors"])
            self.assertIn("forbidden_term:trading", data["errors"])
            self.assertIn("forbidden_term:live_api", data["errors"])

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
