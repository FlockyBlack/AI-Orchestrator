import ast
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LLM_DIR = ROOT / "pm_bot" / "llm"
RUNNER = LLM_DIR / "summarize_actual_manual_llm_response_trial.py"
TRIAL_ARTIFACT = LLM_DIR / "actual_manual_llm_response_trial.v1.json"
OPERATOR_RESPONSE = LLM_DIR / "real_local_market_llm_trial_response_operator.v1.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("actual_manual_llm_response_surface", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ActualManualLlmResponseWorkbenchSurfaceTests(unittest.TestCase):
    def test_default_summary_surfaces_accepted_actual_response_trial(self):
        module = _load_module()
        summary = module.summarize_actual_manual_llm_response_trial()

        self.assertEqual(
            summary["contract_version"],
            "actual_manual_llm_response_workbench_surface.v1",
        )
        self.assertEqual(summary["artifact_path"], "pm_bot/llm/actual_manual_llm_response_trial.v1.json")
        self.assertTrue(summary["artifact_present"])
        self.assertTrue(summary["operator_response_present"])
        self.assertEqual(summary["operator_response_path"], "pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json")
        self.assertEqual(summary["parse_status"], "parsed")
        self.assertEqual(summary["market_id"], "824952")
        self.assertEqual(summary["response_source_type"], "actual_operator_pasted_response")
        self.assertEqual(summary["trial_packet_source_type"], "real_local_market_artifact")
        self.assertEqual(summary["run_status"], "actual_response_accepted")
        self.assertEqual(summary["acceptance_status"], "accepted_for_operator_review")
        self.assertEqual(summary["response_validation_status"], "accepted")
        self.assertEqual(summary["manual_review_status"], "accepted")
        self.assertEqual(summary["quality_gate_status"], "quality_passed")
        self.assertEqual(summary["errors_count"], 0)
        self.assertEqual(summary["warnings_count"], 0)
        self.assertTrue(summary["offline_review_context_only"])
        self.assertTrue(summary["not_truth_source"])
        self.assertTrue(summary["not_trading_advice"])
        self.assertTrue(summary["not_execution_authority"])

    def test_missing_artifact_is_passive_non_blocking(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as directory:
            summary = module.summarize_actual_manual_llm_response_trial(root=Path(directory))

        self.assertFalse(summary["artifact_present"])
        self.assertEqual(summary["artifact_status"], "missing")
        self.assertEqual(summary["parse_status"], "missing")
        self.assertEqual(summary["run_status"], "not_available")
        self.assertEqual(summary["acceptance_status"], "not_available")
        self.assertIn("not available locally", summary["safe_error_summary"][0])
        self.assertTrue(summary["offline_review_context_only"])

    def test_malformed_artifact_is_passive_non_blocking(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            artifact = temp_root / "pm_bot" / "llm" / "actual_manual_llm_response_trial.v1.json"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text("{", encoding="utf-8")

            summary = module.summarize_actual_manual_llm_response_trial(root=temp_root)

        self.assertTrue(summary["artifact_present"])
        self.assertEqual(summary["artifact_status"], "invalid")
        self.assertEqual(summary["parse_status"], "parse_failed")
        self.assertEqual(summary["run_status"], "not_available")
        self.assertIn("could not be read safely", summary["safe_error_summary"][0])

    def test_markdown_includes_offline_warning_and_statuses(self):
        module = _load_module()
        summary = module.summarize_actual_manual_llm_response_trial(
            artifact_path=TRIAL_ARTIFACT,
            operator_response_path=OPERATOR_RESPONSE,
        )
        markdown = module.render_markdown(summary)

        self.assertIn("PMBOT Actual Manual LLM Response Workbench Surface v1", markdown)
        self.assertIn("run_status: actual_response_accepted", markdown)
        self.assertIn("acceptance_status: accepted_for_operator_review", markdown)
        self.assertIn("offline review context only", markdown)
        self.assertIn("not a truth source", markdown)
        self.assertIn("not trading advice", markdown)
        self.assertIn("not execution authority", markdown)

    def test_no_network_llm_browser_runtime_or_order_imports_are_added(self):
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
