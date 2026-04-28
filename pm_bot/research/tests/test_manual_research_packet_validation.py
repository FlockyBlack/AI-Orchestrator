import ast
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "pm_bot" / "research" / "validate_manual_research_packets.py"
FIXTURE = ROOT / "pm_bot" / "research" / "manual_research_packets_fixture.v1.json"
EXPECTED_REPORT = ROOT / "pm_bot" / "research" / "expected_manual_research_packet_validation.v1.json"


def _run_validator(*extra_args):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *extra_args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _load_module():
    spec = importlib.util.spec_from_file_location("manual_research_packet_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_fixture_packets():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["packets"]


def _load_expected():
    return json.loads(EXPECTED_REPORT.read_text(encoding="utf-8"))


def _codes(errors):
    return [item["code"] for item in errors]


class ManualResearchPacketValidationTests(unittest.TestCase):
    def test_default_cli_report_matches_expected_and_returns_invalid_status(self):
        result = _run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout), _load_expected())

    def test_valid_manual_packets_pass(self):
        module = _load_module()
        packets = _load_fixture_packets()
        for index in (0, 1, 2):
            self.assertEqual(module.validate_packet(packets[index]), [], msg=packets[index]["market_id"])

    def test_invalid_packets_fail_with_stable_errors(self):
        module = _load_module()
        invalid_packet = _load_fixture_packets()[3]
        expected_errors = _load_expected()["validation_errors_by_market_id"]["invalid-manual-packet"]
        self.assertEqual(module.validate_packet(invalid_packet), expected_errors)

    def test_stub_only_packets_remain_allowed_but_not_review_ready(self):
        module = _load_module()
        stub_packet = _load_fixture_packets()[0]
        self.assertEqual(stub_packet["completion_status"], "stub_only")
        self.assertEqual(module.validate_packet(stub_packet), [])

        report = module.build_validation_report(FIXTURE)
        self.assertIn("569368", report["valid_market_ids"])
        self.assertNotIn("569368", report["ready_for_operator_review_market_ids"])

    def test_ready_for_operator_review_requires_enough_manual_evidence(self):
        module = _load_module()
        ready_packet = copy.deepcopy(_load_fixture_packets()[2])
        ready_packet["market_id"] = "ready-missing-credible-news"
        ready_packet["evidence_slots"]["credible_news_yes_evidence"] = []

        codes = set(_codes(module.validate_packet(ready_packet)))
        self.assertIn("ready_for_operator_review_insufficient_evidence:credible_news", codes)

    def test_manual_evidence_added_status_passes_with_partial_evidence(self):
        module = _load_module()
        partial_packet = copy.deepcopy(_load_fixture_packets()[1])
        partial_packet["completion_status"] = "manual_evidence_added"

        self.assertEqual(module.validate_packet(partial_packet), [])

    def test_no_trade_order_wallet_or_execution_fields_are_permitted(self):
        module = _load_module()
        packet = copy.deepcopy(_load_fixture_packets()[2])
        packet["market_id"] = "forbidden-fields"
        packet["wallet"] = "not allowed"
        packet["trade"] = "not allowed"
        packet["execution"] = "not allowed"

        codes = set(_codes(module.validate_packet(packet)))
        self.assertIn("forbidden_field:wallet", codes)
        self.assertIn("forbidden_field:trade", codes)
        self.assertIn("forbidden_field:execution", codes)

    def test_output_is_deterministic(self):
        module = _load_module()
        first = module.build_validation_report(FIXTURE)
        second = module.build_validation_report(FIXTURE)
        self.assertEqual(first, second)

        first_cli = _run_validator().stdout
        second_cli = _run_validator().stdout
        self.assertEqual(first_cli, second_cli)

    def test_summary_counts_are_stable(self):
        payload = json.loads(_run_validator().stdout)
        self.assertEqual(payload["total_packets_checked"], 4)
        self.assertEqual(payload["valid_packets"], 3)
        self.assertEqual(payload["invalid_packets"], 1)
        self.assertEqual(payload["ready_for_operator_review"], 1)
        self.assertEqual(payload["needs_more_information"], 1)
        self.assertEqual(payload["validation_errors_by_market_id"].keys(), {"invalid-manual-packet"})

    def test_write_report_uses_requested_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "manual_packet_report.json"
            result = _run_validator("--write-report", str(output_path))
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8")), _load_expected())

    def test_validator_has_no_network_or_api_imports(self):
        source = VALIDATOR.read_text(encoding="utf-8").lower()
        forbidden = [
            "requests",
            "urllib.request",
            "httpx",
            "aiohttp",
            "socket",
            "websocket",
            "py_clob_client",
            "gamma-api",
        ]
        for term in forbidden:
            self.assertNotIn(term, source)

    def test_standard_library_only(self):
        tree = ast.parse(VALIDATOR.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
