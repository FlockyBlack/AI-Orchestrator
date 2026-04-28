import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "codex_auto" / "queue" / "validate_queue_task.py"
READY_TASK = ROOT / "codex_auto" / "tasks" / "ready" / "CODEX-AUTO-TINY-001.task.json"
TMP_DIR = ROOT / "codex_auto" / "tasks" / "ready"


def _run_validator(path: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ValidateQueueTaskTests(unittest.TestCase):
    def test_ready_task_validates(self):
        result = _run_validator(READY_TASK)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "valid")
        self.assertTrue(payload["flocky_validation_required"])

    def test_missing_required_field_fails(self):
        data = json.loads(READY_TASK.read_text(encoding="utf-8"))
        data.pop("approval_ref")
        temp = TMP_DIR / "tmp_missing_queue_field.task.json"
        temp.write_text(json.dumps(data), encoding="utf-8")
        self.addCleanup(lambda: temp.unlink(missing_ok=True))
        result = _run_validator(temp)
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing:approval_ref", payload["errors"])

    def test_runtime_wiring_allowed_true_fails(self):
        data = json.loads(READY_TASK.read_text(encoding="utf-8"))
        data["runtime_wiring_allowed"] = True
        temp = TMP_DIR / "tmp_runtime_wiring.task.json"
        temp.write_text(json.dumps(data), encoding="utf-8")
        self.addCleanup(lambda: temp.unlink(missing_ok=True))
        payload = json.loads(_run_validator(temp).stdout)
        self.assertIn("runtime_wiring_allowed_must_be_false", payload["errors"])

    def test_external_codex_cli_allowed_true_fails(self):
        data = json.loads(READY_TASK.read_text(encoding="utf-8"))
        data["external_codex_cli_allowed"] = True
        temp = TMP_DIR / "tmp_external_cli.task.json"
        temp.write_text(json.dumps(data), encoding="utf-8")
        self.addCleanup(lambda: temp.unlink(missing_ok=True))
        payload = json.loads(_run_validator(temp).stdout)
        self.assertIn("external_codex_cli_allowed_must_be_false", payload["errors"])

    def test_network_api_wallet_private_key_trading_true_fail(self):
        data = json.loads(READY_TASK.read_text(encoding="utf-8"))
        data["network_allowed"] = True
        data["api_allowed"] = True
        data["wallet_allowed"] = True
        data["private_key_allowed"] = True
        data["trading_allowed"] = True
        temp = TMP_DIR / "tmp_forbidden_flags.task.json"
        temp.write_text(json.dumps(data), encoding="utf-8")
        self.addCleanup(lambda: temp.unlink(missing_ok=True))
        payload = json.loads(_run_validator(temp).stdout)
        self.assertIn("network_allowed_must_be_false", payload["errors"])
        self.assertIn("api_allowed_must_be_false", payload["errors"])
        self.assertIn("wallet_allowed_must_be_false", payload["errors"])
        self.assertIn("private_key_allowed_must_be_false", payload["errors"])
        self.assertIn("trading_allowed_must_be_false", payload["errors"])

    def test_allowed_output_outside_allowed_paths_fails(self):
        data = json.loads(READY_TASK.read_text(encoding="utf-8"))
        data["allowed_output"] = "codex_auto/runs/OTHER/fixture_output.json"
        temp = TMP_DIR / "tmp_bad_output.task.json"
        temp.write_text(json.dumps(data), encoding="utf-8")
        self.addCleanup(lambda: temp.unlink(missing_ok=True))
        payload = json.loads(_run_validator(temp).stdout)
        self.assertIn("allowed_output_must_match_approved_tiny_output", payload["errors"])

    def test_missing_approval_ref_fails(self):
        data = json.loads(READY_TASK.read_text(encoding="utf-8"))
        data["approval_ref"] = "codex_auto/fixtures/missing.json"
        temp = TMP_DIR / "tmp_missing_approval.task.json"
        temp.write_text(json.dumps(data), encoding="utf-8")
        self.addCleanup(lambda: temp.unlink(missing_ok=True))
        payload = json.loads(_run_validator(temp).stdout)
        self.assertIn("approval_ref_must_match_approved_tiny_fixture", payload["errors"])
        self.assertIn("approval_ref_missing", payload["errors"])

    def test_missing_forbidden_surfaces_fail(self):
        data = json.loads(READY_TASK.read_text(encoding="utf-8"))
        data["forbidden_paths"] = ["runtime/"]
        temp = TMP_DIR / "tmp_missing_surfaces.task.json"
        temp.write_text(json.dumps(data), encoding="utf-8")
        self.addCleanup(lambda: temp.unlink(missing_ok=True))
        payload = json.loads(_run_validator(temp).stdout)
        self.assertIn("missing_forbidden_path:scripts/dispatcher.py", payload["errors"])
        self.assertIn("missing_forbidden_path:scripts/run_codex.py", payload["errors"])
        self.assertIn("missing_forbidden_path:state/", payload["errors"])
        self.assertIn("missing_protected_surface:checkpoint", payload["errors"])

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
