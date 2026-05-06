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
LLM_DIR = ROOT / "pm_bot" / "llm"
EXPORTER = LLM_DIR / "export_real_local_market_llm_trial.py"
PACKET = LLM_DIR / "real_local_market_llm_trial_packet.v1.json"
PROMPT = LLM_DIR / "real_local_market_llm_trial_prompt.v1.md"
RESPONSE = LLM_DIR / "real_local_market_llm_trial_response_example.v1.json"
RESULT_JSON = LLM_DIR / "real_local_market_llm_trial.v1.json"
RESULT_MD = LLM_DIR / "real_local_market_llm_trial.v1.md"
EXPECTED_RESULT = LLM_DIR / "expected_real_local_market_llm_trial.v1.json"
LOW_QUALITY_RESPONSE = LLM_DIR / "manual_llm_paste_in_response_example_low_quality.v1.json"
VALIDATOR = LLM_DIR / "validate_llm_analysis_artifacts.py"


def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
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


def _imported_roots(source):
    tree = ast.parse(source)
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


class RealLocalMarketLlmTrialTests(unittest.TestCase):
    def test_exporter_selects_real_local_pmbot_artifact_when_available(self):
        module = _load_module(EXPORTER, "pmbot_real_local_trial_select")

        selection = module.select_real_local_market_artifact()

        self.assertEqual(selection["selection_status"], "selected")
        self.assertEqual(selection["trial_packet_source_type"], "real_local_market_artifact")
        self.assertEqual(selection["source_artifact_path"], "pm_bot/research/selected_ingest_final_dossier_drafts.v1.json")
        self.assertEqual(selection["market_id"], "824952")
        self.assertFalse(selection["used_example_packet_fallback"])
        self.assertEqual(selection["source_preference_rank"], 2)
        self.assertFalse(selection["inspected_artifacts"][0]["suitable"])

    def test_exporter_does_not_silently_fall_back_to_example_packet(self):
        module = _load_module(EXPORTER, "pmbot_real_local_trial_no_fallback")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = module.build_trial_result(
                temp_path / "packet.json",
                temp_path / "missing_response.json",
                temp_path / "prompt.md",
                root=temp_path,
            )

        self.assertEqual(result["validation_status"], "blocked")
        self.assertEqual(result["trial_packet_source_type"], "no_suitable_real_local_market_artifact")
        self.assertFalse(result["source_selection"]["used_example_packet_fallback"])
        self.assertNotEqual(result["source_artifact_path"], "pm_bot/llm/example_llm_analysis_packet.v1.json")
        self.assertIn("no_suitable_real_local_market_artifact", _error_codes({"errors": result["warnings"]}))

    def test_exporter_writes_packet_prompt_result_json_and_markdown(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(EXPORTER),
                "--out-packet",
                str(PACKET),
                "--out-prompt",
                str(PROMPT),
                "--response",
                str(RESPONSE),
                "--out-json",
                str(RESULT_JSON),
                "--out-md",
                str(RESULT_MD),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        stdout_result = json.loads(completed.stdout)

        self.assertEqual(stdout_result["validation_status"], "accepted")
        self.assertEqual(stdout_result["trial_packet_source_type"], "real_local_market_artifact")
        self.assertEqual(stdout_result["source_artifact_path"], "pm_bot/research/selected_ingest_final_dossier_drafts.v1.json")
        self.assertEqual(stdout_result["market_id"], "824952")
        self.assertTrue(PACKET.exists())
        self.assertTrue(PROMPT.exists())
        self.assertTrue(RESPONSE.exists())
        self.assertEqual(_load_json(RESULT_JSON), stdout_result)
        markdown = RESULT_MD.read_text(encoding="utf-8")
        self.assertIn("Trial status: accepted", markdown)
        self.assertIn("Manual Operator Steps For A Real Trial", markdown)
        self.assertIn("No API calls", markdown)

    def test_trial_packet_uses_real_source_and_passes_packet_schema(self):
        module = _load_module(EXPORTER, "pmbot_real_local_trial_packet")
        module.export_trial(PACKET, RESPONSE, RESULT_JSON, RESULT_MD, PROMPT)
        validator = _load_module(VALIDATOR, "pmbot_llm_validator_for_real_local_trial")

        packet = _load_json(PACKET)
        result = validator.validate_packet_payload(packet)

        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["errors"], [])
        self.assertEqual(packet["market_context"]["market_id"], "824952")
        self.assertEqual(packet["source_artifacts"][0]["path"], "pm_bot/research/selected_ingest_final_dossier_drafts.v1.json")
        self.assertNotEqual(packet["source_artifacts"][0]["path"], "pm_bot/llm/example_llm_analysis_packet.v1.json")

    def test_trial_prompt_includes_strict_json_instruction_and_forbidden_constraints(self):
        module = _load_module(EXPORTER, "pmbot_real_local_trial_prompt")
        module.export_trial(PACKET, RESPONSE, RESULT_JSON, RESULT_MD, PROMPT)

        prompt = PROMPT.read_text(encoding="utf-8")

        self.assertIn("Return only strict JSON matching `llm_analysis_response_schema.v1.json`.", prompt)
        self.assertIn("Do not wrap the JSON in Markdown.", prompt)
        self.assertIn("Use only this packet content. Do not infer from unstated external data.", prompt)
        for text in (
            "Do not include probability estimates.",
            "Do not include EV.",
            "Do not include edge.",
            "Do not include scoring.",
            "Do not include recommended side.",
            "Also do not include market decisions",
        ):
            self.assertIn(text, prompt)

    def test_valid_example_response_passes_validator_manual_review_and_quality_gate(self):
        module = _load_module(EXPORTER, "pmbot_real_local_trial_valid")

        result = module.build_trial_result(PACKET, RESPONSE, PROMPT)

        self.assertEqual(result["packet_validation"]["status"], "accepted")
        self.assertEqual(result["response_validation"]["status"], "accepted")
        self.assertEqual(result["manual_review_status"], "accepted")
        self.assertIn(result["quality_gate_status"], {"quality_passed", "quality_passed_with_warnings"})
        self.assertEqual(result["validation_status"], "accepted")

    def test_forbidden_recommendation_response_is_rejected(self):
        module = _load_module(EXPORTER, "pmbot_real_local_trial_forbidden")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            response = copy.deepcopy(_load_json(RESPONSE))
            response["recommended_side"] = "Yes"
            response_path = temp_path / "forbidden_response.json"
            prompt_path = temp_path / "trial_prompt.md"
            packet_path = temp_path / "trial_packet.json"
            _write_json(response_path, response)

            result = module.build_trial_result(packet_path, response_path, prompt_path)

        self.assertEqual(result["validation_status"], "rejected")
        self.assertEqual(result["manual_review_status"], "rejected")
        self.assertEqual(result["quality_gate_status"], "quality_failed")
        self.assertIn("forbidden_response_field:recommended_side", _error_codes(result))

    def test_low_quality_response_fails_quality_gate(self):
        module = _load_module(EXPORTER, "pmbot_real_local_trial_low_quality")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            response = copy.deepcopy(_load_json(LOW_QUALITY_RESPONSE))
            response["packet_id"] = "llm-analysis-packet-real-local-market-824952"
            response_path = temp_path / "low_quality_response.json"
            prompt_path = temp_path / "trial_prompt.md"
            packet_path = temp_path / "trial_packet.json"
            _write_json(response_path, response)

            result = module.build_trial_result(packet_path, response_path, prompt_path)

        self.assertEqual(result["manual_review_status"], "accepted")
        self.assertEqual(result["quality_gate_status"], "quality_failed")
        self.assertEqual(result["validation_status"], "rejected")
        self.assertIn("minimum_useful_content_not_met", _error_codes(result))
        self.assertIn("placeholder_text_found", _error_codes(result))

    def test_missing_and_malformed_response_fail_safely(self):
        module = _load_module(EXPORTER, "pmbot_real_local_trial_missing_malformed")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            missing_response = temp_path / "missing_response.json"
            malformed_response = temp_path / "malformed_response.json"
            malformed_response.write_text("{", encoding="utf-8")

            missing_result = module.build_trial_result(
                temp_path / "missing_packet.json",
                missing_response,
                temp_path / "missing_prompt.md",
            )
            malformed_result = module.build_trial_result(
                temp_path / "bad_packet.json",
                malformed_response,
                temp_path / "bad_prompt.md",
            )

        self.assertEqual(missing_result["validation_status"], "rejected")
        self.assertEqual(missing_result["quality_gate_status"], "quality_failed")
        self.assertIn("response_file_missing", _error_codes(missing_result))
        self.assertEqual(malformed_result["validation_status"], "rejected")
        self.assertEqual(malformed_result["quality_gate_status"], "quality_failed")
        self.assertIn("response_json_malformed", _error_codes(malformed_result))

    def test_expected_trial_fixture_matches(self):
        module = _load_module(EXPORTER, "pmbot_real_local_trial_expected")

        result = module.build_trial_result(PACKET, RESPONSE, PROMPT)

        self.assertEqual(result, _load_json(EXPECTED_RESULT))

    def test_exporter_adds_no_network_llm_browser_runtime_or_order_calls(self):
        module = _load_module(EXPORTER, "pmbot_real_local_trial_safety")
        source = EXPORTER.read_text(encoding="utf-8")
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
            "run_operator_workbench_export",
            "run_codex(",
            "scripts/run_codex.py",
            "dispatcher.py",
        ):
            self.assertNotIn(token, source_no_spaces)

        result = module.build_trial_result(PACKET, RESPONSE, PROMPT)
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
