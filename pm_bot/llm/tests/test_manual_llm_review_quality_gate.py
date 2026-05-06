import ast
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LLM_DIR = ROOT / "pm_bot" / "llm"
QUALITY_GATE = LLM_DIR / "evaluate_manual_llm_review_quality_gate.py"
PACKET = LLM_DIR / "example_llm_analysis_packet.v1.json"
VALID_RESPONSE = LLM_DIR / "manual_llm_paste_in_response_example_valid.v1.json"
LOW_QUALITY_RESPONSE = LLM_DIR / "manual_llm_paste_in_response_example_low_quality.v1.json"
UNSAFE_CERTAINTY_RESPONSE = LLM_DIR / "manual_llm_paste_in_response_example_unsafe_certainty.v1.json"
FORBIDDEN_RECOMMENDATION_RESPONSE = LLM_DIR / "manual_llm_paste_in_response_example_invalid.v1.json"
MANUAL_REVIEW = LLM_DIR / "manual_llm_paste_in_review.v1.json"
EXPECTED_GATE = LLM_DIR / "expected_manual_llm_review_quality_gate.v1.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("pmbot_manual_llm_quality_gate", QUALITY_GATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _error_codes(result):
    return {error["code"] for error in result["errors"]}


def _collect_keys(value):
    keys = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.add(key)
            keys.update(_collect_keys(nested))
    elif isinstance(value, list):
        for item in value:
            keys.update(_collect_keys(item))
    return keys


def _imported_roots(source):
    tree = ast.parse(source)
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


class ManualLlmReviewQualityGateTests(unittest.TestCase):
    def test_high_quality_manual_response_passes_quality_gate(self):
        module = _load_module()

        result = module.build_quality_gate(PACKET, VALID_RESPONSE, MANUAL_REVIEW)

        self.assertEqual(result["validation_status"], "quality_passed")
        self.assertEqual(result["base_validator_status"], "accepted")
        self.assertEqual(result["quality_counts"]["checks_failed"], 0)
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["required_sections_check"]["present_sections"])
        self.assertEqual(result["required_sections_check"]["missing_sections"], [])
        self.assertEqual(result["manual_review_input_check"]["status"], "loaded")

    def test_valid_but_low_quality_response_fails_quality_gate(self):
        module = _load_module()

        result = module.build_quality_gate(PACKET, LOW_QUALITY_RESPONSE, MANUAL_REVIEW)
        codes = _error_codes(result)

        self.assertEqual(result["base_validator_status"], "accepted")
        self.assertEqual(result["validation_status"], "quality_failed")
        self.assertIn("minimum_useful_content_not_met", codes)
        self.assertIn("placeholder_text_found", codes)
        self.assertGreater(result["quality_counts"]["checks_failed"], 0)

    def test_unsafe_certainty_response_fails_quality_gate(self):
        module = _load_module()

        result = module.build_quality_gate(PACKET, UNSAFE_CERTAINTY_RESPONSE, MANUAL_REVIEW)
        codes = _error_codes(result)

        self.assertEqual(result["base_validator_status"], "accepted")
        self.assertEqual(result["validation_status"], "quality_failed")
        self.assertTrue(result["unsafe_certainty_check"]["unsafe_certainty_detected"])
        self.assertIn("unsafe_certainty:guaranteed", codes)
        self.assertIn("unsafe_certainty:risk_free", codes)

    def test_forbidden_recommendation_response_fails_through_base_validator(self):
        module = _load_module()

        result = module.build_quality_gate(PACKET, FORBIDDEN_RECOMMENDATION_RESPONSE, MANUAL_REVIEW)
        codes = _error_codes(result)

        self.assertEqual(result["base_validator_status"], "rejected")
        self.assertEqual(result["validation_status"], "quality_failed")
        self.assertIn("forbidden_response_field:recommended_side", codes)
        self.assertTrue(result["forbidden_content_check"]["forbidden_content_detected"])

    def test_missing_required_section_fails(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            response = copy.deepcopy(_load_json(VALID_RESPONSE))
            response.pop("risk_notes")
            response_path = Path(temp_dir) / "missing_section_response.json"
            _write_json(response_path, response)

            result = module.build_quality_gate(PACKET, response_path, MANUAL_REVIEW)
            codes = _error_codes(result)

            self.assertEqual(result["base_validator_status"], "rejected")
            self.assertEqual(result["validation_status"], "quality_failed")
            self.assertIn("schema_missing_required", codes)
            self.assertIn("required_section_missing", codes)

    def test_placeholder_only_arrays_fail(self):
        module = _load_module()

        result = module.build_quality_gate(PACKET, LOW_QUALITY_RESPONSE, MANUAL_REVIEW)
        codes = _error_codes(result)

        self.assertEqual(result["generic_or_placeholder_text_check"]["status"], "failed")
        self.assertIn("placeholder_only_array", codes)

    def test_markdown_and_json_outputs_are_written(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            out_json = Path(temp_dir) / "quality_gate.json"
            out_md = Path(temp_dir) / "quality_gate.md"

            result = module.export_quality_gate(PACKET, VALID_RESPONSE, MANUAL_REVIEW, out_json, out_md)

            self.assertEqual(result["validation_status"], "quality_passed")
            self.assertEqual(_load_json(out_json), result)
            markdown = out_md.read_text(encoding="utf-8")
            self.assertIn("Quality gate status: quality_passed", markdown)
            self.assertIn("Base validator status: accepted", markdown)
            self.assertIn(
                "This is a deterministic offline quality gate. It does not evaluate truth, probability, EV, edge, side, or trade execution.",
                markdown,
            )

    def test_expected_quality_gate_fixture_matches(self):
        module = _load_module()

        result = module.build_quality_gate(PACKET, VALID_RESPONSE, MANUAL_REVIEW)

        self.assertEqual(result, _load_json(EXPECTED_GATE))

    def test_quality_gate_does_not_call_network_llm_browser_or_runtime_services(self):
        source = QUALITY_GATE.read_text(encoding="utf-8")
        imported_roots = _imported_roots(source)

        for token in (
            "requests",
            "urllib",
            "httpx",
            "aiohttp",
            "socket",
            "websocket",
            "webbrowser",
            "selenium",
            "playwright",
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

        module = _load_module()
        result = module.build_quality_gate(PACKET, VALID_RESPONSE, MANUAL_REVIEW)
        self.assertFalse(result["safety_flags"]["network_api"])
        self.assertFalse(result["safety_flags"]["llm_api"])
        self.assertFalse(result["safety_flags"]["browser_automation"])
        self.assertFalse(result["safety_flags"]["prompt_automation"])
        self.assertFalse(result["safety_flags"]["runtime_wiring"])

    def test_no_market_decision_fields_are_introduced(self):
        module = _load_module()

        result = module.build_quality_gate(PACKET, VALID_RESPONSE, MANUAL_REVIEW)
        keys = _collect_keys(result)

        self.assertNotIn("quality_score_summary", keys)
        self.assertNotIn("recommended_side", keys)
        self.assertNotIn("probability", keys)
        self.assertNotIn("implied_probability", keys)
        self.assertNotIn("ev", keys)
        self.assertNotIn("edge", keys)
        self.assertNotIn("side_recommendation", keys)
        self.assertFalse(result["safety_flags"]["probability_ev_scoring_or_edge"])
        self.assertFalse(result["safety_flags"]["side_recommendations"])
        self.assertFalse(result["safety_flags"]["market_decision_logic"])
        self.assertFalse(result["safety_flags"]["truth_evaluation"])


if __name__ == "__main__":
    unittest.main()
