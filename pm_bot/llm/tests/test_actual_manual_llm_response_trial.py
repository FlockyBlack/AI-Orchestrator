import ast
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LLM_DIR = ROOT / "pm_bot" / "llm"
RUNNER = LLM_DIR / "run_actual_manual_llm_response_trial.py"
TRIAL = LLM_DIR / "real_local_market_llm_trial.v1.json"
PACKET = LLM_DIR / "real_local_market_llm_trial_packet.v1.json"
PROMPT = LLM_DIR / "real_local_market_llm_trial_prompt.v1.md"
EXAMPLE_RESPONSE = LLM_DIR / "real_local_market_llm_trial_response_example.v1.json"
LOW_QUALITY_RESPONSE = LLM_DIR / "manual_llm_paste_in_response_example_low_quality.v1.json"
EXPECTED_PENDING = LLM_DIR / "expected_actual_manual_llm_response_trial_pending.v1.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("pmbot_actual_manual_llm_response_trial", RUNNER)
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
    response["response_id"] = "llm-analysis-response-real-local-market-operator-010-valid"
    response_path = temp_path / "real_local_market_llm_trial_response_operator.v1.json"
    _write_json(response_path, response)
    return response_path


class ActualManualLlmResponseTrialTests(unittest.TestCase):
    def test_missing_operator_response_returns_pending_operator_input(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_response = Path(temp_dir) / "real_local_market_llm_trial_response_operator.v1.json"

            result = module.build_actual_manual_llm_response_trial(TRIAL, PACKET, PROMPT, missing_response)

        self.assertEqual(result["run_status"], "pending_operator_input")
        self.assertFalse(result["operator_response_present"])
        self.assertEqual(result["next_safe_operator_action"], "save_actual_operator_pasted_response")
        self.assertIn("operator_response_file_missing", _warning_codes(result))

    def test_missing_operator_response_does_not_create_fake_actual_response(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_response = Path(temp_dir) / "real_local_market_llm_trial_response_operator.v1.json"

            module.build_actual_manual_llm_response_trial(TRIAL, PACKET, PROMPT, missing_response)

            self.assertFalse(missing_response.exists())

    def test_missing_operator_response_keeps_acceptance_pending_real_manual_response(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_response = Path(temp_dir) / "real_local_market_llm_trial_response_operator.v1.json"

            result = module.build_actual_manual_llm_response_trial(TRIAL, PACKET, PROMPT, missing_response)

        self.assertEqual(result["acceptance_status"], "pending_real_manual_response")
        self.assertEqual(result["response_validation_status"], "not_run")
        self.assertEqual(result["manual_review_status"], "not_run")
        self.assertEqual(result["quality_gate_status"], "not_run")

    def test_valid_actual_operator_response_is_accepted(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            response_path = _operator_response_fixture(Path(temp_dir))

            result = module.build_actual_manual_llm_response_trial(TRIAL, PACKET, PROMPT, response_path)

        self.assertEqual(result["run_status"], "actual_response_accepted")
        self.assertEqual(result["acceptance_status"], "accepted_for_operator_review")
        self.assertEqual(result["packet_validation_status"], "accepted")
        self.assertEqual(result["response_validation_status"], "accepted")
        self.assertEqual(result["manual_review_status"], "accepted")
        self.assertIn(result["quality_gate_status"], {"quality_passed", "quality_passed_with_warnings"})

    def test_forbidden_actual_operator_response_is_rejected(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            response = copy.deepcopy(_load_json(EXAMPLE_RESPONSE))
            response["response_id"] = "llm-analysis-response-real-local-market-operator-010-forbidden"
            response["recommended_side"] = "Yes"
            response_path = Path(temp_dir) / "forbidden_response.json"
            _write_json(response_path, response)

            result = module.build_actual_manual_llm_response_trial(TRIAL, PACKET, PROMPT, response_path)

        self.assertEqual(result["run_status"], "actual_response_rejected")
        self.assertEqual(result["acceptance_status"], "rejected")
        self.assertIn("forbidden_response_field:recommended_side", _error_codes(result))
        self.assertIn("forbidden_content_detected", _error_codes(result))

    def test_low_quality_actual_operator_response_is_not_accepted(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            response = copy.deepcopy(_load_json(LOW_QUALITY_RESPONSE))
            response["response_id"] = "llm-analysis-response-real-local-market-operator-010-low-quality"
            response["packet_id"] = _load_json(PACKET)["packet_id"]
            response_path = Path(temp_dir) / "low_quality_response.json"
            _write_json(response_path, response)

            result = module.build_actual_manual_llm_response_trial(TRIAL, PACKET, PROMPT, response_path)

        self.assertEqual(result["run_status"], "actual_response_rejected")
        self.assertNotEqual(result["acceptance_status"], "accepted_for_operator_review")
        self.assertEqual(result["quality_gate_status"], "quality_failed")
        self.assertIn("quality_gate_not_passed", _error_codes(result))

    def test_malformed_actual_operator_response_is_blocked_safely(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            response_path = Path(temp_dir) / "malformed_response.json"
            response_path.write_text("{", encoding="utf-8")

            result = module.build_actual_manual_llm_response_trial(TRIAL, PACKET, PROMPT, response_path)

        self.assertEqual(result["run_status"], "actual_response_blocked")
        self.assertEqual(result["acceptance_status"], "blocked")
        self.assertIn("response_json_malformed", _error_codes(result))

    def test_non_real_packet_source_is_rejected_or_blocked(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            trial = copy.deepcopy(_load_json(TRIAL))
            trial["trial_packet_source_type"] = "example_packet_trial_not_live_market"
            trial_path = temp_path / "non_real_trial.json"
            response_path = _operator_response_fixture(temp_path)
            _write_json(trial_path, trial)

            result = module.build_actual_manual_llm_response_trial(trial_path, PACKET, PROMPT, response_path)

        self.assertIn(result["run_status"], {"actual_response_rejected", "actual_response_blocked"})
        self.assertIn("trial_packet_source_type_not_real_local_market_artifact", _error_codes(result))

    def test_example_packet_fallback_true_is_rejected_or_blocked(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            trial = copy.deepcopy(_load_json(TRIAL))
            trial["source_selection"]["used_example_packet_fallback"] = True
            trial_path = temp_path / "fallback_trial.json"
            response_path = _operator_response_fixture(temp_path)
            _write_json(trial_path, trial)

            result = module.build_actual_manual_llm_response_trial(trial_path, PACKET, PROMPT, response_path)

        self.assertIn(result["run_status"], {"actual_response_rejected", "actual_response_blocked"})
        self.assertIn("used_example_packet_fallback_true", _error_codes(result))

    def test_json_and_markdown_outputs_are_written(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            missing_response = temp_path / "real_local_market_llm_trial_response_operator.v1.json"
            out_json = temp_path / "actual_trial.json"
            out_md = temp_path / "actual_trial.md"

            result = module.export_actual_manual_llm_response_trial(
                TRIAL, PACKET, PROMPT, missing_response, out_json, out_md
            )

            self.assertEqual(_load_json(out_json), result)
            markdown = out_md.read_text(encoding="utf-8")
            self.assertIn("Run status: pending_operator_input", markdown)
            self.assertIn("Actual operator response file exists: False", markdown)
            self.assertIn("no API, no automation", markdown)

    def test_expected_pending_fixture_matches(self):
        module = _load_module()

        result = module.build_actual_manual_llm_response_trial()

        self.assertEqual(result, _load_json(EXPECTED_PENDING))

    def test_no_network_llm_browser_prompt_runtime_or_order_calls_are_added(self):
        module = _load_module()
        source = RUNNER.read_text(encoding="utf-8")
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

        result = module.build_actual_manual_llm_response_trial()
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
