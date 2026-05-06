import ast
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LLM_DIR = ROOT / "pm_bot" / "llm"
EXPORTER = LLM_DIR / "export_offline_llm_review_stub.py"
VALIDATOR = LLM_DIR / "validate_llm_analysis_artifacts.py"
PACKET = LLM_DIR / "example_llm_analysis_packet.v1.json"
VALID_RESPONSE = LLM_DIR / "example_llm_analysis_response_valid.v1.json"
INVALID_RECOMMENDATION_RESPONSE = LLM_DIR / "example_llm_analysis_response_invalid_forbidden_recommendation.v1.json"
INVALID_PHRASE_RESPONSE = LLM_DIR / "example_llm_analysis_response_invalid_forbidden_phrase.v1.json"
EXPECTED_STUB = LLM_DIR / "expected_offline_llm_review_stub.v1.json"


def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _error_codes(result):
    return {error["code"] for error in result["errors"]}


class ExportOfflineLlmReviewStubTests(unittest.TestCase):
    def test_exporter_accepts_valid_packet_response(self):
        module = _load_module(EXPORTER, "pmbot_offline_llm_review_stub")
        result = module.build_review_stub(PACKET, VALID_RESPONSE)

        self.assertEqual(result["validation_status"], "accepted")
        self.assertEqual(result["packet_validation"]["status"], "accepted")
        self.assertEqual(result["response_validation"]["status"], "accepted")
        self.assertEqual(result["errors"], [])
        self.assertFalse(result["forbidden_content_detected"]["detected"])

    def test_exporter_rejects_forbidden_recommendation_field(self):
        module = _load_module(EXPORTER, "pmbot_offline_llm_review_stub")
        result = module.build_review_stub(PACKET, INVALID_RECOMMENDATION_RESPONSE)

        self.assertEqual(result["validation_status"], "rejected")
        self.assertEqual(result["packet_validation"]["status"], "accepted")
        self.assertEqual(result["response_validation"]["status"], "rejected")
        self.assertIn("forbidden_response_field:recommended_side", _error_codes(result))
        self.assertIn("schema_unexpected_field", _error_codes(result))
        self.assertTrue(result["forbidden_content_detected"]["detected"])

    def test_exporter_rejects_forbidden_trading_phrase(self):
        module = _load_module(EXPORTER, "pmbot_offline_llm_review_stub")
        result = module.build_review_stub(PACKET, INVALID_PHRASE_RESPONSE)

        self.assertEqual(result["validation_status"], "rejected")
        self.assertIn("forbidden_phrase:place_order", _error_codes(result))
        self.assertTrue(result["forbidden_content_detected"]["detected"])

    def test_exporter_writes_json_and_markdown_outputs(self):
        module = _load_module(EXPORTER, "pmbot_offline_llm_review_stub")
        with tempfile.TemporaryDirectory() as temp_dir:
            out_json = Path(temp_dir) / "review.json"
            out_md = Path(temp_dir) / "review.md"

            result = module.export_review_stub(PACKET, VALID_RESPONSE, out_json, out_md)

            self.assertEqual(result["validation_status"], "accepted")
            self.assertEqual(_load_json(out_json), result)
            markdown = out_md.read_text(encoding="utf-8")
            self.assertIn("Status: accepted", markdown)
            self.assertIn("offline stub only", markdown)
            self.assertIn("not trading advice", markdown)

    def test_exporter_result_matches_expected_fixture(self):
        module = _load_module(EXPORTER, "pmbot_offline_llm_review_stub")
        result = module.build_review_stub(PACKET, VALID_RESPONSE)

        self.assertEqual(result, _load_json(EXPECTED_STUB))

    def test_exporter_rejects_missing_or_malformed_artifacts(self):
        module = _load_module(EXPORTER, "pmbot_offline_llm_review_stub")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            malformed_packet = temp_path / "malformed_packet.json"
            malformed_response = temp_path / "malformed_response.json"
            missing_packet = temp_path / "missing_packet.json"
            missing_response = temp_path / "missing_response.json"
            malformed_packet.write_text("{", encoding="utf-8")
            malformed_response.write_text("{", encoding="utf-8")

            packet_result = module.build_review_stub(malformed_packet, VALID_RESPONSE)
            response_result = module.build_review_stub(PACKET, malformed_response)
            missing_packet_result = module.build_review_stub(missing_packet, VALID_RESPONSE)
            missing_response_result = module.build_review_stub(PACKET, missing_response)

            self.assertEqual(packet_result["validation_status"], "rejected")
            self.assertIn("packet_json_malformed", _error_codes(packet_result))
            self.assertEqual(response_result["validation_status"], "rejected")
            self.assertIn("response_json_malformed", _error_codes(response_result))
            self.assertEqual(missing_packet_result["validation_status"], "rejected")
            self.assertIn("packet_file_missing", _error_codes(missing_packet_result))
            self.assertEqual(missing_response_result["validation_status"], "rejected")
            self.assertIn("response_file_missing", _error_codes(missing_response_result))

    def test_exporter_does_not_require_network_llm_runtime_or_workbench(self):
        source = EXPORTER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

        for token in (
            "requests",
            "urllib",
            "httpx",
            "aiohttp",
            "socket",
            "websocket",
            "openai",
            "anthropic",
            "py_clob_client",
            "subprocess",
        ):
            self.assertNotIn(token, imported_roots)
        for token in (
            "run_operator_workbench_export",
            "run_codex",
            "dispatcher",
            "create_order",
            "submit_order",
        ):
            self.assertNotIn(token, source)

    def test_existing_llm_001_validator_behavior_is_preserved(self):
        validator = _load_module(VALIDATOR, "pmbot_llm_validator")

        accepted = validator.validate_artifacts(PACKET, VALID_RESPONSE)
        rejected = validator.validate_artifacts(PACKET, INVALID_RECOMMENDATION_RESPONSE)
        rejected_codes = {error["code"] for error in rejected["errors"]}

        self.assertEqual(accepted["status"], "accepted")
        self.assertEqual(rejected["status"], "rejected")
        self.assertIn("forbidden_response_field:recommended_side", rejected_codes)


if __name__ == "__main__":
    unittest.main()
