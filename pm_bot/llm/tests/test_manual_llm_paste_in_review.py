import ast
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LLM_DIR = ROOT / "pm_bot" / "llm"
PROMPT_EXPORTER = LLM_DIR / "export_manual_llm_prompt.py"
MANUAL_REVIEW_VALIDATOR = LLM_DIR / "validate_manual_llm_paste_in_review.py"
PACKET = LLM_DIR / "example_llm_analysis_packet.v1.json"
VALID_RESPONSE = LLM_DIR / "manual_llm_paste_in_response_example_valid.v1.json"
INVALID_RESPONSE = LLM_DIR / "manual_llm_paste_in_response_example_invalid.v1.json"
PROMPT = LLM_DIR / "manual_llm_prompt.v1.md"
EXPECTED_REVIEW = LLM_DIR / "expected_manual_llm_paste_in_review.v1.json"


def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
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


def _imported_roots(source):
    tree = ast.parse(source)
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


class ManualLlmPasteInReviewTests(unittest.TestCase):
    def test_prompt_exporter_writes_markdown_prompt(self):
        module = _load_module(PROMPT_EXPORTER, "pmbot_manual_llm_prompt_exporter")
        with tempfile.TemporaryDirectory() as temp_dir:
            out_md = Path(temp_dir) / "manual_prompt.md"

            result = module.export_manual_prompt(PACKET, out_md)

            self.assertEqual(result["status"], "accepted")
            self.assertTrue(out_md.exists())
            markdown = out_md.read_text(encoding="utf-8")
            self.assertIn("# PMBOT Manual LLM Paste-In Prompt v1", markdown)
            self.assertIn("offline analysis only", markdown)
            self.assertIn("not trading advice", markdown)

    def test_prompt_includes_schema_return_instruction(self):
        module = _load_module(PROMPT_EXPORTER, "pmbot_manual_llm_prompt_exporter_schema")

        prompt, packet_validation = module.render_manual_prompt(PACKET)

        self.assertEqual(packet_validation["status"], "accepted")
        self.assertIn("Return only strict JSON matching `llm_analysis_response_schema.v1.json`.", prompt)
        self.assertIn('"contract_version": {', prompt)
        self.assertIn('"const": "llm_analysis_response.v1"', prompt)

    def test_prompt_includes_forbidden_output_constraints(self):
        module = _load_module(PROMPT_EXPORTER, "pmbot_manual_llm_prompt_exporter_constraints")

        prompt, _packet_validation = module.render_manual_prompt(PACKET)

        for text in (
            "probability estimates",
            "EV",
            "edge",
            "scoring",
            "recommended side",
            "bet recommendations",
            "order size",
            "price target",
            "execution instruction",
            "wallet/private-key/credential handling",
            "certainty claims",
        ):
            self.assertIn(text, prompt)

    def test_prompt_omits_unsafe_runtime_payloads(self):
        module = _load_module(PROMPT_EXPORTER, "pmbot_manual_llm_prompt_exporter_safe")

        prompt, _packet_validation = module.render_manual_prompt(PACKET)

        self.assertIn("Use only this packet content", prompt)
        for token in (
            "Authorization:",
            "Bearer ",
            "api_key",
            "private_key",
            "seed_phrase",
            "wallet_address",
            "curl ",
            "requests.",
            "openai.",
            "py_clob_client",
            "create_order",
            "submit_order",
        ):
            self.assertNotIn(token, prompt)

    def test_prompt_output_is_deterministic(self):
        module = _load_module(PROMPT_EXPORTER, "pmbot_manual_llm_prompt_exporter_deterministic")

        first_prompt, first_validation = module.render_manual_prompt(PACKET)
        second_prompt, second_validation = module.render_manual_prompt(PACKET)

        self.assertEqual(first_prompt, second_prompt)
        self.assertEqual(first_validation, second_validation)

    def test_prompt_exporter_refuses_invalid_packet(self):
        module = _load_module(PROMPT_EXPORTER, "pmbot_manual_llm_prompt_exporter_invalid_packet")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            invalid_packet = copy.deepcopy(_load_json(PACKET))
            invalid_packet["operator_questions"].append("Should the operator bet on either outcome?")
            invalid_packet_path = temp_path / "invalid_packet.json"
            out_md = temp_path / "manual_prompt.md"
            _write_json(invalid_packet_path, invalid_packet)

            with self.assertRaises(module.ManualPromptExportError) as raised:
                module.export_manual_prompt(invalid_packet_path, out_md)

            self.assertIn("forbidden_phrase:bet_on", {error["code"] for error in raised.exception.errors})
            self.assertFalse(out_md.exists())

    def test_manual_review_accepts_valid_response(self):
        module = _load_module(MANUAL_REVIEW_VALIDATOR, "pmbot_manual_llm_review")

        result = module.build_manual_review(PACKET, VALID_RESPONSE, PROMPT)

        self.assertEqual(result["validation_status"], "accepted")
        self.assertEqual(result["packet_validation"]["status"], "accepted")
        self.assertEqual(result["response_validation"]["status"], "accepted")
        self.assertEqual(result["missing_sections"], [])
        self.assertFalse(result["forbidden_content_detected"]["detected"])

    def test_manual_review_rejects_forbidden_recommendation_and_phrase(self):
        module = _load_module(MANUAL_REVIEW_VALIDATOR, "pmbot_manual_llm_review_invalid")

        result = module.build_manual_review(PACKET, INVALID_RESPONSE, PROMPT)
        codes = _error_codes(result)

        self.assertEqual(result["validation_status"], "rejected")
        self.assertIn("forbidden_response_field:recommended_side", codes)
        self.assertIn("forbidden_phrase:place_order", codes)
        self.assertTrue(result["forbidden_content_detected"]["detected"])

    def test_manual_review_rejects_forbidden_phrase_only_response(self):
        module = _load_module(MANUAL_REVIEW_VALIDATOR, "pmbot_manual_llm_review_phrase")
        with tempfile.TemporaryDirectory() as temp_dir:
            response = copy.deepcopy(_load_json(VALID_RESPONSE))
            response["risk_notes"].append("Place order after this review note.")
            response_path = Path(temp_dir) / "forbidden_phrase_response.json"
            _write_json(response_path, response)

            result = module.build_manual_review(PACKET, response_path, PROMPT)

            self.assertEqual(result["validation_status"], "rejected")
            self.assertIn("forbidden_phrase:place_order", _error_codes(result))
            self.assertTrue(result["forbidden_content_detected"]["detected"])

    def test_manual_review_rejects_malformed_response_json(self):
        module = _load_module(MANUAL_REVIEW_VALIDATOR, "pmbot_manual_llm_review_malformed")
        with tempfile.TemporaryDirectory() as temp_dir:
            malformed_response = Path(temp_dir) / "malformed_response.json"
            malformed_response.write_text("{", encoding="utf-8")

            result = module.build_manual_review(PACKET, malformed_response, PROMPT)

            self.assertEqual(result["validation_status"], "rejected")
            self.assertIn("response_json_malformed", _error_codes(result))
            self.assertEqual(result["packet_validation"]["status"], "accepted")

    def test_manual_review_writes_json_and_markdown(self):
        module = _load_module(MANUAL_REVIEW_VALIDATOR, "pmbot_manual_llm_review_export")
        with tempfile.TemporaryDirectory() as temp_dir:
            out_json = Path(temp_dir) / "manual_review.json"
            out_md = Path(temp_dir) / "manual_review.md"

            result = module.export_manual_review(PACKET, VALID_RESPONSE, out_json, out_md, PROMPT)

            self.assertEqual(result["validation_status"], "accepted")
            self.assertEqual(_load_json(out_json), result)
            markdown = out_md.read_text(encoding="utf-8")
            self.assertIn("Status: accepted", markdown)
            self.assertIn("manual llm paste-in only", markdown.lower())
            self.assertIn("not trading advice", markdown)
            self.assertIn("autonomous action", result["operator_summary"])

    def test_manual_review_result_matches_expected_fixture(self):
        module = _load_module(MANUAL_REVIEW_VALIDATOR, "pmbot_manual_llm_review_expected")

        result = module.build_manual_review(PACKET, VALID_RESPONSE, PROMPT)

        self.assertEqual(result, _load_json(EXPECTED_REVIEW))

    def test_manual_tools_do_not_require_network_llm_browser_or_runtime_services(self):
        prompt_source = PROMPT_EXPORTER.read_text(encoding="utf-8")
        review_source = MANUAL_REVIEW_VALIDATOR.read_text(encoding="utf-8")
        imported_roots = _imported_roots(prompt_source) | _imported_roots(review_source)

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
            self.assertNotIn(token, prompt_source)
            self.assertNotIn(token, review_source)

        module = _load_module(MANUAL_REVIEW_VALIDATOR, "pmbot_manual_llm_review_services")
        result = module.build_manual_review(PACKET, VALID_RESPONSE, PROMPT)
        self.assertFalse(result["safety_flags"]["network_api"])
        self.assertFalse(result["safety_flags"]["llm_api"])
        self.assertFalse(result["safety_flags"]["runtime_wiring"])
        self.assertFalse(result["safety_flags"]["prompt_automation"])


if __name__ == "__main__":
    unittest.main()
