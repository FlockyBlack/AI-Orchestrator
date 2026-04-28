import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "operator" / "review_manual_command_inbox.py"
INBOX = ROOT / "pm_bot" / "operator" / "manual_command_inbox_fixture.v1.json"
EXPECTED_JSON = ROOT / "pm_bot" / "operator" / "expected_manual_command_inbox_review.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "operator" / "manual_command_inbox_review.v1.md"


def _load_runner():
    import importlib.util

    spec = importlib.util.spec_from_file_location("pmbot_manual_command_inbox_review", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _run_json(*extra_args):
    return subprocess.run(
        [sys.executable, str(RUNNER), *extra_args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _run_markdown():
    return subprocess.run(
        [sys.executable, str(RUNNER), "--markdown"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


class ManualCommandInboxReviewTests(unittest.TestCase):
    def test_json_output_matches_expected(self):
        self.assertEqual(json.loads(_run_json().stdout), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_matches_expected(self):
        self.assertEqual(_run_markdown().stdout, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_review_counts_and_inert_authority(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["records_seen"], 7)
        self.assertEqual(payload["accepted_count"], 3)
        self.assertEqual(payload["rejected_count"], 3)
        self.assertEqual(payload["needs_human_review_count"], 1)
        self.assertFalse(payload["execution_authority"])
        self.assertEqual(payload["commands_executed"], 0)
        self.assertEqual(payload["orders_created"], 0)
        self.assertEqual(payload["network_calls"], 0)

    def test_rejected_records_include_validator_reasons(self):
        payload = json.loads(_run_json().stdout)
        rejected = {record["command_id"]: record for record in payload["rejected_records"]}
        self.assertIn("invalid_source_type:telegram_live_bot", rejected["manual-inbox-invalid-live-source"]["rejection_reasons"])
        self.assertIn("forbidden_source_type:telegram_live_bot", rejected["manual-inbox-invalid-live-source"]["rejection_reasons"])
        self.assertIn("execution_authority_must_be_false", rejected["manual-inbox-invalid-authority"]["rejection_reasons"])
        self.assertIn("requires_human_review_must_be_true", rejected["manual-inbox-invalid-authority"]["rejection_reasons"])
        self.assertIn("safety_flag_must_be_false:command_execution", rejected["manual-inbox-invalid-authority"]["rejection_reasons"])
        self.assertIn("unexpected_payload_field:edge", rejected["manual-inbox-invalid-scoring"]["rejection_reasons"])
        self.assertIn("forbidden_field_name:payload.probability", rejected["manual-inbox-invalid-scoring"]["rejection_reasons"])

    def test_needs_human_review_records_remain_separate_and_inert(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual([record["command_id"] for record in payload["needs_human_review_records"]], ["manual-inbox-human-review-001"])
        record = payload["needs_human_review_records"][0]
        self.assertEqual(record["operator_next_action_label"], "needs_human_review_only")
        self.assertFalse(record["execution_authority"])
        self.assertTrue(record["requires_human_review"])

    def test_custom_inbox_rejects_unsafe_added_record(self):
        fixture = json.loads(INBOX.read_text(encoding="utf-8"))
        unsafe = copy.deepcopy(fixture["records"][0])
        unsafe["command_id"] = "manual-inbox-invalid-runtime-field"
        unsafe["webhook_url"] = "https://example.invalid/pmbot"
        fixture["records"] = [unsafe]

        with tempfile.TemporaryDirectory() as directory:
            inbox_path = Path(directory) / "inbox.json"
            inbox_path.write_text(json.dumps(fixture), encoding="utf-8")
            payload = json.loads(_run_json("--inbox", str(inbox_path)).stdout)

        self.assertEqual(payload["accepted_count"], 0)
        self.assertEqual(payload["rejected_count"], 1)
        reasons = payload["rejected_records"][0]["rejection_reasons"]
        self.assertIn("unexpected_top_level_field:webhook_url", reasons)
        self.assertIn("forbidden_field_name:webhook_url", reasons)
        self.assertIn("credential_shape_present:webhook_url", reasons)

    def test_standard_library_only_and_no_runtime_surfaces(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "pathlib"})
        self.assertTrue(
            imports.isdisjoint(
                {
                    "requests",
                    "urllib",
                    "httpx",
                    "socket",
                    "telegram",
                    "web3",
                    "subprocess",
                    "asyncio",
                }
            )
        )

        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertTrue(calls.isdisjoint({"open", "exec", "eval", "compile", "__import__"}))


if __name__ == "__main__":
    unittest.main()
