import ast
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "pm_bot" / "operator" / "manual_command_contract.v1.json"
EXAMPLES_PATH = ROOT / "pm_bot" / "operator" / "manual_command_examples.v1.json"
RUNNER = ROOT / "pm_bot" / "operator" / "validate_manual_command_contract.py"


def _load_validator():
    import importlib.util

    spec = importlib.util.spec_from_file_location("pmbot_manual_command_validator", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ManualCommandContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = _load_validator()
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.examples = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))

    def test_contract_declares_inert_manual_boundaries(self):
        self.assertTrue(self.contract["deterministic"])
        self.assertTrue(self.contract["local_file_reads_only"])
        self.assertTrue(self.contract["manual_review_only"])
        self.assertTrue(self.contract["record_is_inert"])
        self.assertTrue(self.contract["runtime_integration_required_before_use"])
        self.assertFalse(self.contract["explicit_non_authority"]["commands_execute_actions"])
        self.assertFalse(self.contract["explicit_non_authority"]["commands_place_orders"])
        self.assertFalse(self.contract["explicit_non_authority"]["commands_call_apis"])
        self.assertIn("telegram_transcript_placeholder", self.contract["allowed_source_types"])
        self.assertIn("telegram_live_bot", self.contract["forbidden_source_types"])

    def test_valid_examples_pass(self):
        for command in self.examples["valid_commands"]:
            with self.subTest(command_id=command["command_id"]):
                self.assertEqual(self.validator.validate_command(command, self.contract), [])

    def test_unsafe_examples_are_rejected_with_expected_reasons(self):
        for example in self.examples["invalid_commands"]:
            command = example["command"]
            errors = self.validator.validate_command(command, self.contract)
            with self.subTest(case_id=example["case_id"]):
                self.assertTrue(errors)
                for expected in example["expected_reject_reasons"]:
                    self.assertTrue(
                        any(error == expected or error.startswith(f"{expected}:") for error in errors),
                        f"{expected} not found in {errors}",
                    )

    def test_validator_rejects_added_trading_and_scoring_fields(self):
        command = copy.deepcopy(self.examples["valid_commands"][0])
        command["payload"]["side"] = "YES"
        command["payload"]["probability"] = 0.51
        command["payload"]["ev"] = 0.01
        errors = self.validator.validate_command(command, self.contract)
        self.assertTrue(any(error.startswith("unexpected_payload_field:side") for error in errors))
        self.assertTrue(any(error.startswith("forbidden_field_name:payload.side") for error in errors))
        self.assertTrue(any(error.startswith("forbidden_field_name:payload.probability") for error in errors))
        self.assertTrue(any(error.startswith("forbidden_field_name:payload.ev") for error in errors))

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
        self.assertEqual(payload["valid_examples_checked"], 6)
        self.assertEqual(payload["invalid_examples_checked"], 8)

    def test_standard_library_only(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "re", "sys"})


if __name__ == "__main__":
    unittest.main()
