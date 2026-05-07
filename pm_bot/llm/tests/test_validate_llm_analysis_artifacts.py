import ast
import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LLM_DIR = ROOT / "pm_bot" / "llm"
VALIDATOR = LLM_DIR / "validate_llm_analysis_artifacts.py"
PACKET = LLM_DIR / "example_llm_analysis_packet.v1.json"
VALID_RESPONSE = LLM_DIR / "example_llm_analysis_response_valid.v1.json"
INVALID_RECOMMENDATION_RESPONSE = LLM_DIR / "example_llm_analysis_response_invalid_forbidden_recommendation.v1.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("pmbot_llm_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class ValidateLlmAnalysisArtifactsTests(unittest.TestCase):
    def test_valid_packet_passes(self):
        module = _load_module()
        result = module.validate_packet_payload(_load_json(PACKET))

        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["errors"], [])

    def test_valid_response_passes(self):
        module = _load_module()
        result = module.validate_response_payload(_load_json(VALID_RESPONSE))

        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["errors"], [])

    def test_response_with_forbidden_recommendation_field_fails(self):
        module = _load_module()
        result = module.validate_response_payload(_load_json(INVALID_RECOMMENDATION_RESPONSE))
        codes = {error["code"] for error in result["errors"]}

        self.assertEqual(result["status"], "rejected")
        self.assertIn("forbidden_response_field:recommended_side", codes)
        self.assertIn("schema_unexpected_field", codes)

    def test_response_with_forbidden_trading_phrase_fails(self):
        module = _load_module()
        response = copy.deepcopy(_load_json(VALID_RESPONSE))
        response["risk_notes"].append("Place order after this review note.")

        result = module.validate_response_payload(response)
        codes = {error["code"] for error in result["errors"]}

        self.assertEqual(result["status"], "rejected")
        self.assertIn("forbidden_phrase:place_order", codes)

    def test_response_forbidden_phrase_error_reports_sanitized_acceptance_diagnostic(self):
        module = _load_module()
        response = copy.deepcopy(_load_json(VALID_RESPONSE))
        checklist_index = len(response["operator_review_checklist"])
        response["operator_review_checklist"].append(
            "Check for any market-specific edge cases in official rules."
        )

        result = module.validate_response_payload(response)
        errors = [error for error in result["errors"] if error["code"] == "forbidden_phrase:edge"]

        self.assertEqual(result["status"], "rejected")
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(error["gate_id"], "response_schema")
        self.assertEqual(error["detector_rule_id"], "forbidden_phrase:edge")
        self.assertEqual(error["forbidden_phrase"], "edge")
        self.assertEqual(error["field_path"], f"operator_review_checklist[{checklist_index}]")
        self.assertEqual(error["checked_content_source"], "parsed_response_payload")
        self.assertEqual(error["diagnostic_classification"], "false_positive_contextual_phrase")
        self.assertEqual(error["diagnostic_reason_code"], "neutral_edge_case_phrase_preserve_block")
        self.assertIn("[redacted:safety-term]", error["safe_redacted_excerpt"])
        self.assertNotIn("edge", error["safe_redacted_excerpt"].lower())

    def test_packet_with_forbidden_output_request_fails(self):
        module = _load_module()
        packet = copy.deepcopy(_load_json(PACKET))
        packet["operator_questions"].append("Should the operator bet on either outcome?")

        result = module.validate_packet_payload(packet)
        codes = {error["code"] for error in result["errors"]}

        self.assertEqual(result["status"], "rejected")
        self.assertIn("forbidden_phrase:bet_on", codes)

    def test_validator_does_not_require_network_or_runtime_services(self):
        module = _load_module()
        report = module.validate_artifacts(PACKET, VALID_RESPONSE)
        source = VALIDATOR.read_text(encoding="utf-8")

        self.assertEqual(report["status"], "accepted")
        self.assertTrue(report["checks"]["standard_library_only"])
        self.assertTrue(report["checks"]["local_only_validator"])
        self.assertFalse(report["checks"]["llm_api_calls"])
        self.assertFalse(report["checks"]["network_api_calls"])
        self.assertFalse(report["checks"]["runtime_wiring"])
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

    def test_json_schemas_and_examples_parse_deterministically(self):
        json_paths = sorted(LLM_DIR.glob("*.json"))
        self.assertTrue(json_paths)

        first_pass = {path.name: _load_json(path) for path in json_paths}
        second_pass = {path.name: _load_json(path) for path in json_paths}
        self.assertEqual(first_pass, second_pass)

        self.assertIn("llm_analysis_packet_schema.v1.json", first_pass)
        self.assertIn("llm_analysis_response_schema.v1.json", first_pass)
        self.assertIn("example_llm_analysis_packet.v1.json", first_pass)
        self.assertIn("example_llm_analysis_response_valid.v1.json", first_pass)


if __name__ == "__main__":
    unittest.main()
