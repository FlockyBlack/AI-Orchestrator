import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "codex_auto" / "ready_promotion" / "validate_ready_promotion.py"
MANIFEST = ROOT / "codex_auto" / "tasks" / "ready" / "PMBOT-BATCH-001.ready_manifest.json"


def _run_validator(path: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ValidateReadyPromotionTests(unittest.TestCase):
    def test_ready_manifest_validates(self):
        result = _run_validator(MANIFEST)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "valid")
        self.assertEqual(len(payload["ready_task_results"]), 6)

    def test_all_six_ready_task_files_validate(self):
        payload = json.loads(_run_validator(MANIFEST).stdout)
        self.assertTrue(all(item["status"] == "valid" for item in payload["ready_task_results"]))

    def test_approved_for_execution_true_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manifest.json"
            payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
            ready_path = ROOT / payload["ready_task_refs"][0]
            ready_payload = json.loads(ready_path.read_text(encoding="utf-8"))
            ready_payload["approved_for_execution"] = True
            temp_ready = Path(temp_dir) / "ready.task.json"
            temp_ready.write_text(json.dumps(ready_payload), encoding="utf-8")
            payload["ready_task_refs"][0] = str(temp_ready.relative_to(ROOT)) if temp_ready.is_relative_to(ROOT) else str(temp_ready)
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = _run_validator(path)
            data = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("approved_for_execution_must_be_false", data["errors"])

    def test_manifest_level_false_flags_and_missing_requirements_fail(self):
        cases = [
            ("execution_allowed_now", True, "execution_allowed_now_must_be_false"),
            ("external_codex_cli_allowed_now", True, "external_codex_cli_allowed_now_must_be_false"),
            ("runtime_wiring_allowed", True, "runtime_wiring_allowed_must_be_false"),
            ("human_approval_required_before_execution", False, "human_approval_required_before_execution_must_be_true"),
            ("flocky_review_required_before_execution", False, "flocky_review_required_before_execution_must_be_true"),
        ]
        for field, value, error in cases:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as temp_dir:
                    path = Path(temp_dir) / "manifest.json"
                    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
                    payload[field] = value
                    path.write_text(json.dumps(payload), encoding="utf-8")
                    result = _run_validator(path)
                    data = json.loads(result.stdout)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(error, data["errors"])

    def test_final_done_claim_runtime_truth_and_network_wallet_trading_scope_fail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manifest.json"
            payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
            ready_path = ROOT / payload["ready_task_refs"][0]
            ready_payload = json.loads(ready_path.read_text(encoding="utf-8"))
            ready_payload["summary"] = "final flocky done runtime truth"
            ready_payload["allowed_scope"] = ["network api wallet private key trading real order"]
            temp_ready = Path(temp_dir) / "ready.task.json"
            temp_ready.write_text(json.dumps(ready_payload), encoding="utf-8")
            payload["ready_task_refs"][0] = str(temp_ready)
            payload["ready_manifest_ref"] = str(path)
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = _run_validator(path)
            data = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("content:final_done_claim_forbidden", data["errors"])
            self.assertIn("content:runtime_truth_claim_forbidden", data["errors"])
            self.assertIn("allowed_scope:network_forbidden", data["errors"])
            self.assertIn("allowed_scope:api_forbidden", data["errors"])
            self.assertIn("allowed_scope:wallet_forbidden", data["errors"])
            self.assertIn("allowed_scope:private_key_forbidden", data["errors"])
            self.assertIn("allowed_scope:trading_forbidden", data["errors"])

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
