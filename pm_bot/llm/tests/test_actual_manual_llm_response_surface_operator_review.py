import ast
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LLM_DIR = ROOT / "pm_bot" / "llm"
RUNNER = LLM_DIR / "evaluate_actual_manual_llm_response_surface_operator_review.py"
OUT_JSON = LLM_DIR / "actual_manual_llm_response_surface_operator_review.v1.json"
OUT_MD = LLM_DIR / "actual_manual_llm_response_surface_operator_review.v1.md"
EXPECTED_JSON = LLM_DIR / "expected_actual_manual_llm_response_surface_operator_review.v1.json"
DOC_RESULT = ROOT / "docs" / "PMBOT_LLM_012_RESULT.json"
DOC_MD = ROOT / "docs" / "PMBOT_LLM_012_OPERATOR_REVIEW_ACTUAL_MANUAL_LLM_RESPONSE_SURFACE.md"


def _load_module():
    spec = importlib.util.spec_from_file_location("pmbot_llm_012_surface_review", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _accepted_surface():
    return {
        "contract_version": "actual_manual_llm_response_workbench_surface.v1",
        "generated_by": "pm_bot/llm/summarize_actual_manual_llm_response_trial.py",
        "artifact_path": "pm_bot/llm/actual_manual_llm_response_trial.v1.json",
        "artifact_present": True,
        "artifact_status": "present",
        "parse_status": "parsed",
        "operator_response_path": "pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json",
        "operator_response_present": True,
        "trial_artifact_operator_response_present": True,
        "market_id": "824952",
        "source_artifact_path": "pm_bot/research/selected_ingest_final_dossier_drafts.v1.json",
        "response_source_type": "actual_operator_pasted_response",
        "trial_packet_source_type": "real_local_market_artifact",
        "run_status": "actual_response_accepted",
        "acceptance_status": "accepted_for_operator_review",
        "packet_validation_status": "accepted",
        "response_validation_status": "accepted",
        "manual_review_status": "accepted",
        "quality_gate_status": "quality_passed",
        "errors_count": 0,
        "warnings_count": 0,
        "next_safe_operator_action": (
            "Review the accepted local artifacts as offline operator context only; "
            "do not execute or automate anything."
        ),
        "safe_error_summary": [],
        "safety_flags": {
            "offline_review_context_only": True,
            "not_truth_source": True,
            "not_trading_advice": True,
            "not_execution_authority": True,
            "surface_only": True,
            "local_file_reads_only": True,
            "deterministic": True,
            "runtime_wiring": False,
            "network_api": False,
            "llm_api": False,
            "browser_automation": False,
            "prompt_automation": False,
            "credentials_or_wallet": False,
            "real_orders_or_live_trading": False,
            "autonomous_paper_orders": False,
            "probability_ev_scoring_or_edge": False,
            "side_recommendations": False,
            "market_decision_logic": False,
            "truth_evaluation": False,
        },
        "offline_review_context_only": True,
        "not_truth_source": True,
        "not_trading_advice": True,
        "not_execution_authority": True,
        "explicit_operator_warning": (
            "This surface is offline review context only. It is not a truth source, "
            "not trading advice, and not execution authority."
        ),
        "surface_only": True,
        "llm_text_generated": False,
        "llm_api_calls_added": False,
        "browser_automation_added": False,
        "runtime_integration_added": False,
    }


def _surface_markdown(surface):
    return "\n".join(
        [
            "# Temp Surface",
            "",
            "## Actual Manual LLM Response Trial",
            "",
            f"- artifact_path: {surface['artifact_path']}",
            f"- artifact_present: {str(surface['artifact_present']).lower()}",
            f"- operator_response_path: {surface['operator_response_path']}",
            f"- operator_response_present: {str(surface['operator_response_present']).lower()}",
            f"- response_source_type: {surface['response_source_type']}",
            f"- market_id: {surface['market_id']}",
            f"- source_artifact_path: {surface['source_artifact_path']}",
            f"- run_status: {surface['run_status']}",
            f"- acceptance_status: {surface['acceptance_status']}",
            f"- response_validation_status: {surface['response_validation_status']}",
            f"- manual_review_status: {surface['manual_review_status']}",
            f"- quality_gate_status: {surface['quality_gate_status']}",
            f"- errors_count: {surface['errors_count']}",
            f"- warnings_count: {surface['warnings_count']}",
            f"- next_safe_operator_action: {surface['next_safe_operator_action']}",
            f"- explicit_warning: {surface['explicit_operator_warning']}",
            "",
            "## After Section",
            "",
        ]
    )


def _write_surface_artifacts(root, surface):
    pack_json = root / "pm_bot" / "workbench" / "operator_review_pack.v1.json"
    export_json = root / "pm_bot" / "workbench" / "operator_workbench_export_run.v1.json"
    pack_md = root / "pm_bot" / "workbench" / "operator_review_pack.v1.md"
    export_md = root / "pm_bot" / "workbench" / "operator_workbench_export_run.v1.md"
    _write_json(pack_json, {"actual_manual_llm_response_trial": surface})
    _write_json(export_json, {"actual_manual_llm_response_trial": surface})
    pack_md.parent.mkdir(parents=True, exist_ok=True)
    markdown = _surface_markdown(surface)
    pack_md.write_text(markdown, encoding="utf-8")
    export_md.write_text(markdown, encoding="utf-8")


class ActualManualLlmResponseSurfaceOperatorReviewTests(unittest.TestCase):
    def test_accepted_surface_passes(self):
        module = _load_module()

        result = module.evaluate_operator_surface_review()

        self.assertEqual(result["operator_surface_review_status"], "operator_surface_review_passed")
        self.assertEqual(result["review_counts"]["errors_count"], 0)
        self.assertEqual(result["surface_snapshots"]["operator_review_pack"]["market_id"], "824952")
        self.assertEqual(
            result["surface_snapshots"]["operator_workbench_export"]["response_source_type"],
            "actual_operator_pasted_response",
        )
        self.assertTrue(result["safety_flags"]["offline_local_manual_only"])
        self.assertFalse(result["safety_flags"]["llm_api"])
        self.assertFalse(result["safety_flags"]["network_api"])

    def test_missing_workbench_operator_artifact_fails(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            surface = _accepted_surface()
            pack_json = temp_root / "pm_bot" / "workbench" / "operator_review_pack.v1.json"
            pack_md = temp_root / "pm_bot" / "workbench" / "operator_review_pack.v1.md"
            _write_json(pack_json, {"actual_manual_llm_response_trial": surface})
            pack_md.parent.mkdir(parents=True, exist_ok=True)
            pack_md.write_text(_surface_markdown(surface), encoding="utf-8")

            result = module.evaluate_operator_surface_review(root=temp_root)

        self.assertEqual(result["operator_surface_review_status"], "operator_surface_review_failed")
        codes = {error["code"] for error in result["errors"]}
        self.assertIn("operator_workbench_export_json_missing", codes)
        self.assertIn("operator_workbench_export_markdown_missing", codes)

    def test_rejected_or_failed_status_does_not_pass(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            surface = _accepted_surface()
            surface["run_status"] = "actual_response_rejected"
            surface["acceptance_status"] = "rejected"
            surface["response_validation_status"] = "rejected"
            _write_surface_artifacts(temp_root, surface)

            result = module.evaluate_operator_surface_review(root=temp_root)

        self.assertEqual(result["operator_surface_review_status"], "operator_surface_review_failed")
        codes = {error["code"] for error in result["errors"]}
        self.assertIn("operator_review_pack_run_status_unexpected", codes)
        self.assertIn("operator_workbench_export_acceptance_status_unexpected", codes)

    def test_forbidden_phrase_in_surface_text_fails(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            surface = copy.deepcopy(_accepted_surface())
            surface["operator_instruction"] = "Buy this market now."
            _write_surface_artifacts(temp_root, surface)

            result = module.evaluate_operator_surface_review(root=temp_root)

        self.assertEqual(result["operator_surface_review_status"], "operator_surface_review_failed")
        findings = result["checks"]["forbidden_behavior_check"]["forbidden_findings"]
        self.assertTrue(any(item["path"].endswith("operator_instruction") for item in findings))

    def test_markdown_contains_readable_operator_summary_and_safety_boundary(self):
        module = _load_module()
        result = module.evaluate_operator_surface_review()

        markdown = module.render_markdown(result)

        self.assertIn("PMBOT LLM 012 Operator Surface Review", markdown)
        self.assertIn("operator_surface_review_status: operator_surface_review_passed", markdown)
        self.assertIn("market_id: 824952", markdown)
        self.assertIn("response_source_type: actual_operator_pasted_response", markdown)
        self.assertIn("run_status: actual_response_accepted", markdown)
        self.assertIn("acceptance_status: accepted_for_operator_review", markdown)
        self.assertIn("This review is offline review context only.", markdown)
        self.assertIn("It is not a truth source.", markdown)
        self.assertIn("It is not trading advice.", markdown)
        self.assertIn("It is not execution authority.", markdown)

    def test_json_output_is_deterministic_and_matches_expected_fixture(self):
        module = _load_module()

        result = module.export_operator_surface_review()
        second = module.evaluate_operator_surface_review()

        self.assertEqual(result, second)
        self.assertEqual(_load_json(OUT_JSON), result)
        self.assertEqual(_load_json(EXPECTED_JSON), result)
        self.assertEqual(_load_json(DOC_RESULT)["operator_surface_review_status"], result["operator_surface_review_status"])
        self.assertTrue(OUT_MD.exists())
        self.assertTrue(DOC_MD.exists())

    def test_runner_uses_standard_library_and_no_runtime_network_or_order_calls(self):
        source = RUNNER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "sys"})
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


if __name__ == "__main__":
    unittest.main()
