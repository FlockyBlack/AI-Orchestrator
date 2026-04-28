import ast
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "pm_bot" / "operator" / "review_pack_command_bridge_contract.v1.json"
EXAMPLES_PATH = ROOT / "pm_bot" / "operator" / "review_pack_command_bridge_examples.v1.json"
EXAMPLES_MD_PATH = ROOT / "pm_bot" / "operator" / "review_pack_command_bridge_examples.v1.md"
RUNNER = ROOT / "pm_bot" / "operator" / "validate_review_pack_command_bridge.py"


def _load_validator():
    import importlib.util

    spec = importlib.util.spec_from_file_location("pmbot_review_pack_command_bridge_validator", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ReviewPackCommandBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = _load_validator()
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.examples = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))

    def test_contract_declares_inert_non_runtime_boundaries(self):
        self.assertTrue(self.contract["deterministic"])
        self.assertTrue(self.contract["local_file_reads_only"])
        self.assertTrue(self.contract["bridge_is_inert"])
        self.assertTrue(self.contract["manual_review_only"])
        self.assertFalse(self.contract["requires_workbench_001_output"])
        self.assertFalse(self.contract["requires_quality_001_output"])
        self.assertFalse(self.contract["execution_authority"])
        self.assertFalse(self.contract["can_trigger_runtime"])
        self.assertEqual(self.contract["commands_executed"], 0)
        self.assertEqual(self.contract["orders_created"], 0)
        self.assertEqual(self.contract["network_calls"], 0)
        for key, value in self.contract["explicit_non_authority"].items():
            with self.subTest(non_authority=key):
                self.assertFalse(value)

    def test_contract_mapping_coverage(self):
        command_types = {item["command_type"] for item in self.contract["bridge_mappings"]}
        section_ids = {item["review_pack_section_id"] for item in self.contract["bridge_mappings"]}
        self.assertEqual(command_types, set(self.contract["allowed_command_types"]))
        self.assertEqual(section_ids, set(self.contract["review_pack_section_ids"]))
        for mapping in self.contract["bridge_mappings"]:
            with self.subTest(mapping=mapping):
                self.assertTrue(mapping["requires_human_review"])
                self.assertFalse(mapping["execution_authority"])
                self.assertFalse(mapping["can_trigger_runtime"])

    def test_valid_examples_pass(self):
        for record in self.examples["valid_bridge_records"]:
            with self.subTest(bridge_id=record["bridge_id"]):
                self.assertEqual(self.validator.validate_bridge_record(record, self.contract), [])

    def test_invalid_examples_are_rejected_with_expected_reasons(self):
        for example in self.examples["invalid_bridge_records"]:
            record = example["record"]
            errors = self.validator.validate_bridge_record(record, self.contract)
            with self.subTest(case_id=example["case_id"]):
                self.assertTrue(errors)
                for expected in example["expected_reject_reasons"]:
                    self.assertTrue(
                        any(error == expected or error.startswith(f"{expected}:") for error in errors),
                        f"{expected} not found in {errors}",
                    )

    def test_validator_rejects_injected_runtime_trading_and_scoring_fields(self):
        record = copy.deepcopy(self.examples["valid_bridge_records"][0])
        record["webhook_url"] = "https://example.invalid/runtime"
        record["wallet_private_key"] = "-----BEGIN PRIVATE KEY----- fixture -----END PRIVATE KEY-----"
        record["order_id"] = "paper-order-001"
        record["probability"] = 0.51
        record["ev"] = 0.01
        record["edge"] = 0.02
        errors = self.validator.validate_bridge_record(record, self.contract)
        self.assertIn("unexpected_top_level_field:webhook_url", errors)
        self.assertIn("forbidden_field_name:webhook_url", errors)
        self.assertIn("credential_shape_present:webhook_url", errors)
        self.assertIn("forbidden_field_name:wallet_private_key", errors)
        self.assertIn("credential_shape_present:wallet_private_key", errors)
        self.assertIn("forbidden_field_name:order_id", errors)
        self.assertIn("forbidden_field_name:probability", errors)
        self.assertIn("forbidden_field_name:ev", errors)
        self.assertIn("forbidden_field_name:edge", errors)

    def test_validator_cli_checks_examples(self):
        result = subprocess.run(
            [sys.executable, str(RUNNER), str(EXAMPLES_PATH), "--examples"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["valid_examples_checked"], 7)
        self.assertEqual(payload["invalid_examples_checked"], 7)

    def test_markdown_examples_document_static_scope(self):
        content = EXAMPLES_MD_PATH.read_text(encoding="utf-8")
        self.assertIn("request_status_summary", content)
        self.assertIn("missing_stale_artifact_warnings", content)
        self.assertIn("execute operator commands", content)
        self.assertIn("can_trigger_runtime: false", content)

    def test_standard_library_only_and_no_runtime_surfaces(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "re", "sys"})
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
