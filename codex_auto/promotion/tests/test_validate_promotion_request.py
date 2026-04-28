import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "codex_auto" / "promotion" / "validate_promotion_request.py"
REQUEST = ROOT / "codex_auto" / "tasks" / "promotion_requests" / "PMBOT-BATCH-001.promotion_request.json"


def _run_validator(path: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ValidatePromotionRequestTests(unittest.TestCase):
    def test_promotion_request_validates(self):
        result = _run_validator(REQUEST)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "valid")

    def test_promotion_request_fails_if_execution_allowed_now_true(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "request.json"
            payload = json.loads(REQUEST.read_text(encoding="utf-8"))
            payload["execution_allowed_now"] = True
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = _run_validator(path)
            data = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("execution_allowed_now_must_be_false", data["errors"])

    def test_promotion_request_fails_if_runtime_wiring_allowed_true(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "request.json"
            payload = json.loads(REQUEST.read_text(encoding="utf-8"))
            payload["runtime_wiring_allowed"] = True
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = _run_validator(path)
            data = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("runtime_wiring_allowed_must_be_false", data["errors"])

    def test_promotion_request_fails_if_external_codex_cli_allowed_now_true(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "request.json"
            payload = json.loads(REQUEST.read_text(encoding="utf-8"))
            payload["external_codex_cli_allowed_now"] = True
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = _run_validator(path)
            data = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("external_codex_cli_allowed_now_must_be_false", data["errors"])

    def test_promotion_request_fails_if_candidate_ref_escapes_candidates_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "request.json"
            payload = json.loads(REQUEST.read_text(encoding="utf-8"))
            payload["candidate_task_refs"][0] = "docs/PM_BOT_SAFE_BACKLOG_V1.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = _run_validator(path)
            data = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("candidate_ref_outside_candidates:docs/PM_BOT_SAFE_BACKLOG_V1.json", data["errors"])

    def test_scripts_import_no_dispatcher_or_run_codex_or_runtime_modules(self):
        source = VALIDATOR.read_text(encoding="utf-8").lower()
        self.assertNotIn("import dispatcher", source)
        self.assertNotIn("from dispatcher", source)
        self.assertNotIn("import run_codex", source)
        self.assertNotIn("from run_codex", source)
        self.assertNotIn("runtime loop", source)

    def test_scripts_do_not_use_network_api_wallet_private_key_or_trading(self):
        source = VALIDATOR.read_text(encoding="utf-8").lower()
        self.assertNotIn("requests", source)
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("socket", source)

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
