import ast
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LLM_DIR = ROOT / "pm_bot" / "llm"
ACCEPTANCE = LLM_DIR / "evaluate_real_manual_llm_trial_operator_acceptance.py"
TRIAL = LLM_DIR / "real_local_market_llm_trial.v1.json"
PACKET = LLM_DIR / "real_local_market_llm_trial_packet.v1.json"
PROMPT = LLM_DIR / "real_local_market_llm_trial_prompt.v1.md"
EXAMPLE_RESPONSE = LLM_DIR / "real_local_market_llm_trial_response_example.v1.json"
LOW_QUALITY_RESPONSE = LLM_DIR / "manual_llm_paste_in_response_example_low_quality.v1.json"
EXPECTED_RESULT = LLM_DIR / "expected_real_manual_llm_trial_operator_acceptance.v1.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("pmbot_real_manual_llm_operator_acceptance", ACCEPTANCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _error_codes(result):
    return {error["code"] for error in result["errors"]}


def _warning_codes(result):
    return {warning["code"] for warning in result["warnings"]}


def _imported_roots(source):
    tree = ast.parse(source)
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def _operator_response_fixture(temp_path):
    response = copy.deepcopy(_load_json(EXAMPLE_RESPONSE))
    response["response_id"] = "llm-analysis-response-real-local-market-operator-001"
    response_path = temp_path / "real_local_market_llm_trial_response_operator.v1.json"
    _write_json(response_path, response)
    return response_path


class RealManualLlmTrialOperatorAcceptanceTests(unittest.TestCase):
    def test_example_fixture_response_is_pending_not_accepted(self):
        module = _load_module()

        result = module.build_acceptance(TRIAL, PACKET, PROMPT, EXAMPLE_RESPONSE, "example_fixture_response")

        self.assertEqual(result["acceptance_status"], "pending_real_manual_response")
        self.assertNotEqual(result["acceptance_status"], "accepted_for_operator_review")
        self.assertEqual(result["response_source_type"], "example_fixture_response")
        self.assertIn("example_fixture_response_pending_real_manual_response", _warning_codes(result))

    def test_actual_operator_pasted_response_with_valid_response_is_accepted(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            response_path = _operator_response_fixture(Path(temp_dir))

            result = module.build_acceptance(TRIAL, PACKET, PROMPT, response_path, "actual_operator_pasted_response")

        self.assertEqual(result["acceptance_status"], "accepted_for_operator_review")
        self.assertEqual(result["packet_validation_status"], "accepted")
        self.assertEqual(result["response_validation_status"], "accepted")
        self.assertEqual(result["manual_review_status"], "accepted")
        self.assertIn(result["quality_gate_status"], {"quality_passed", "quality_passed_with_warnings"})

    def test_unknown_response_source_type_is_rejected(self):
        module = _load_module()

        result = module.build_acceptance(TRIAL, PACKET, PROMPT, EXAMPLE_RESPONSE, "unknown_source")

        self.assertEqual(result["acceptance_status"], "rejected")
        self.assertIn("response_source_type_unknown", _error_codes(result))

    def test_non_real_packet_source_is_rejected(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            trial = copy.deepcopy(_load_json(TRIAL))
            trial["trial_packet_source_type"] = "example_packet_trial_not_live_market"
            trial_path = Path(temp_dir) / "non_real_trial.json"
            response_path = _operator_response_fixture(Path(temp_dir))
            _write_json(trial_path, trial)

            result = module.build_acceptance(
                trial_path, PACKET, PROMPT, response_path, "actual_operator_pasted_response"
            )

        self.assertEqual(result["acceptance_status"], "rejected")
        self.assertIn("trial_packet_source_type_not_real_local_market_artifact", _error_codes(result))

    def test_example_packet_fallback_true_is_rejected(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            trial = copy.deepcopy(_load_json(TRIAL))
            trial["source_selection"]["used_example_packet_fallback"] = True
            trial_path = Path(temp_dir) / "fallback_trial.json"
            response_path = _operator_response_fixture(Path(temp_dir))
            _write_json(trial_path, trial)

            result = module.build_acceptance(
                trial_path, PACKET, PROMPT, response_path, "actual_operator_pasted_response"
            )

        self.assertEqual(result["acceptance_status"], "rejected")
        self.assertIn("used_example_packet_fallback_true", _error_codes(result))

    def test_forbidden_recommendation_response_is_rejected(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            response = copy.deepcopy(_load_json(EXAMPLE_RESPONSE))
            response["response_id"] = "llm-analysis-response-real-local-market-operator-forbidden-001"
            response["recommended_side"] = "Yes"
            response_path = Path(temp_dir) / "forbidden_response.json"
            _write_json(response_path, response)

            result = module.build_acceptance(
                TRIAL, PACKET, PROMPT, response_path, "actual_operator_pasted_response"
            )

        self.assertEqual(result["acceptance_status"], "rejected")
        self.assertIn("forbidden_response_field:recommended_side", _error_codes(result))
        self.assertIn("forbidden_content_detected", _error_codes(result))

    def test_low_quality_response_is_rejected(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            response = copy.deepcopy(_load_json(LOW_QUALITY_RESPONSE))
            response["response_id"] = "llm-analysis-response-real-local-market-operator-low-quality-001"
            response["packet_id"] = _load_json(PACKET)["packet_id"]
            response_path = Path(temp_dir) / "low_quality_response.json"
            _write_json(response_path, response)

            result = module.build_acceptance(
                TRIAL, PACKET, PROMPT, response_path, "actual_operator_pasted_response"
            )

        self.assertEqual(result["acceptance_status"], "rejected")
        self.assertEqual(result["quality_gate_status"], "quality_failed")
        self.assertIn("quality_gate_not_passed", _error_codes(result))

    def test_missing_or_malformed_artifacts_block_safely(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            missing_trial = temp_path / "missing_trial.json"
            malformed_response = temp_path / "malformed_response.json"
            malformed_response.write_text("{", encoding="utf-8")

            missing_result = module.build_acceptance(
                missing_trial, PACKET, PROMPT, EXAMPLE_RESPONSE, "example_fixture_response"
            )
            malformed_result = module.build_acceptance(
                TRIAL, PACKET, PROMPT, malformed_response, "actual_operator_pasted_response"
            )

        self.assertEqual(missing_result["acceptance_status"], "blocked")
        self.assertIn("trial_file_missing", _error_codes(missing_result))
        self.assertEqual(malformed_result["acceptance_status"], "blocked")
        self.assertIn("response_json_malformed", _error_codes(malformed_result))

    def test_acceptance_json_and_markdown_outputs_are_written(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            out_json = temp_path / "acceptance.json"
            out_md = temp_path / "acceptance.md"

            result = module.export_acceptance(
                TRIAL,
                PACKET,
                PROMPT,
                EXAMPLE_RESPONSE,
                "example_fixture_response",
                out_json,
                out_md,
            )

            self.assertEqual(_load_json(out_json), result)
            markdown = out_md.read_text(encoding="utf-8")
            self.assertIn("Acceptance status: pending_real_manual_response", markdown)
            self.assertIn("no API", markdown)
            self.assertIn("no trading advice", markdown)

    def test_expected_fixture_matches(self):
        module = _load_module()

        result = module.build_acceptance(TRIAL, PACKET, PROMPT, EXAMPLE_RESPONSE, "example_fixture_response")

        self.assertEqual(result, _load_json(EXPECTED_RESULT))

    def test_no_network_llm_browser_prompt_automation_runtime_or_order_calls_are_added(self):
        module = _load_module()
        source = ACCEPTANCE.read_text(encoding="utf-8")
        imported_roots = _imported_roots(source)

        self.assertLessEqual(imported_roots, {"argparse", "json", "pathlib", "pm_bot", "sys"})
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

        source_no_spaces = source.lower().replace(" ", "")
        for token in (
            "requests.",
            "httpx.",
            "urllib.request",
            "socket.",
            "webbrowser.",
            "selenium.",
            "playwright.",
            "openai.",
            "anthropic.",
            "create_order(",
            "submit_order(",
            "place_order(",
            "run_codex(",
            "scripts/run_codex.py",
            "dispatcher.py",
        ):
            self.assertNotIn(token, source_no_spaces)

        result = module.build_acceptance(TRIAL, PACKET, PROMPT, EXAMPLE_RESPONSE, "example_fixture_response")
        for flag in (
            "runtime_wiring",
            "network_api",
            "llm_api",
            "browser_automation",
            "prompt_automation",
            "credentials_or_wallet",
            "real_orders_or_live_trading",
            "autonomous_paper_orders",
            "probability_ev_scoring_or_edge",
            "side_recommendations",
            "market_decision_logic",
            "truth_evaluation",
            "dispatcher_or_run_codex_changed",
        ):
            self.assertFalse(result["safety_flags"][flag])


if __name__ == "__main__":
    unittest.main()
