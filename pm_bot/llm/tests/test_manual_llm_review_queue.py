import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LLM_DIR = ROOT / "pm_bot" / "llm"
RUNNER = LLM_DIR / "export_manual_llm_review_queue.py"
QUEUE_JSON = LLM_DIR / "manual_llm_review_queue.v1.json"
QUEUE_MD = LLM_DIR / "manual_llm_review_queue.v1.md"
EXPECTED_JSON = LLM_DIR / "expected_manual_llm_review_queue.v1.json"
DOC_RESULT = ROOT / "docs" / "PMBOT_LLM_014_RESULT.json"
DOC_MD = ROOT / "docs" / "PMBOT_LLM_014_MANUAL_PACKET_QUEUE_EXPANSION.md"
PACKET = LLM_DIR / "real_local_market_llm_trial_packet.v1.json"
PROMPT = LLM_DIR / "real_local_market_llm_trial_prompt.v1.md"
SELECTED_DOSSIERS = ROOT / "pm_bot" / "research" / "selected_ingest_final_dossier_drafts.v1.json"
INVALID_RESPONSE = LLM_DIR / "example_llm_analysis_response_invalid_forbidden_recommendation.v1.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("manual_llm_review_queue", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run_exporter():
    return subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _candidate(**overrides):
    candidate = {
        "candidate_id": "test_candidate_824952",
        "candidate_source": "unit_test",
        "market_id": "824952",
        "source_artifact_path": str(SELECTED_DOSSIERS),
        "packet_path": str(PACKET),
        "prompt_path": str(PROMPT),
        "operator_response_path": "",
    }
    candidate.update(overrides)
    return candidate


class ManualLlmReviewQueueTests(unittest.TestCase):
    def test_default_accepted_market_appears_as_response_accepted_for_operator_review(self):
        module = _load_module()

        queue = module.build_manual_llm_review_queue(ROOT)

        self.assertEqual(queue["queue_items_total"], 15)
        item = next(item for item in queue["items"] if item["market_id"] == "824952")
        self.assertEqual(item["market_id"], "824952")
        self.assertEqual(item["review_queue_status"], "response_accepted_for_operator_review")
        self.assertTrue(item["response_present"])
        self.assertEqual(item["validation_status"], "accepted")
        self.assertEqual(item["quality_gate_status"], "quality_passed")
        self.assertEqual(item["operator_surface_review_status"], "operator_surface_review_passed")
        self.assertTrue(item["offline_manual_only"])
        self.assertTrue(item["not_truth_source"])
        self.assertTrue(item["not_trading_advice"])
        self.assertTrue(item["not_execution_authority"])

    def test_additional_safe_local_candidates_are_included_from_approved_artifacts(self):
        module = _load_module()

        queue = module.build_manual_llm_review_queue(ROOT)
        market_ids = [item["market_id"] for item in queue["items"]]
        added_market_ids = queue["candidate_discovery"]["added_candidate_market_ids"]

        self.assertIn("563650", market_ids)
        self.assertIn("692258", market_ids)
        self.assertIn("563650", added_market_ids)
        self.assertIn("692258", added_market_ids)
        self.assertEqual(queue["queue_status_counts"]["ready_for_manual_packet_export"], 14)
        self.assertEqual(queue["candidate_discovery"]["additional_ready_candidates_found"], 14)
        self.assertTrue(
            all(
                item["review_queue_status"] == "ready_for_manual_packet_export"
                for item in queue["items"]
                if item["market_id"] != "824952"
            )
        )

    def test_duplicate_market_ids_are_deduplicated_with_source_count(self):
        module = _load_module()

        queue = module.build_manual_llm_review_queue(
            ROOT,
            candidates=[
                _candidate(candidate_id="first", candidate_source_type="unit_test_first"),
                _candidate(candidate_id="second", candidate_source_type="unit_test_second"),
            ],
        )

        self.assertEqual(queue["queue_items_total"], 1)
        item = queue["items"][0]
        self.assertEqual(item["market_id"], "824952")
        self.assertEqual(item["source_count"], 2)
        self.assertEqual(
            item["candidate_source_types"],
            ["unit_test_first", "unit_test_second"],
        )

    def test_local_candidate_without_packet_is_ready_for_manual_packet_export(self):
        module = _load_module()

        queue = module.build_manual_llm_review_queue(
            ROOT,
            candidates=[
                _candidate(
                    candidate_id="research_only_111",
                    candidate_source_type="unit_test_research_artifact",
                    market_id="111",
                    packet_path="",
                    prompt_path="",
                    operator_response_path="",
                )
            ],
        )

        item = queue["items"][0]
        self.assertFalse(item["packet_present"])
        self.assertEqual(item["review_queue_status"], "ready_for_manual_packet_export")

    def test_packet_without_prompt_is_ready_for_manual_prompt_export(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_prompt = Path(temp_dir) / "missing_prompt.md"

            queue = module.build_manual_llm_review_queue(
                ROOT,
                candidates=[_candidate(prompt_path=str(missing_prompt))],
            )

        item = queue["items"][0]
        self.assertTrue(item["packet_present"])
        self.assertFalse(item["prompt_present"])
        self.assertEqual(item["review_queue_status"], "ready_for_manual_prompt_export")

    def test_missing_response_item_waits_for_operator_pasted_response(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_response = Path(temp_dir) / "missing_response.json"

            queue = module.build_manual_llm_review_queue(
                ROOT,
                candidates=[_candidate(operator_response_path=str(missing_response))],
            )

        item = queue["items"][0]
        self.assertFalse(item["response_present"])
        self.assertEqual(item["review_queue_status"], "waiting_for_operator_pasted_response")
        self.assertEqual(item["packet_validation_status"], "accepted")
        self.assertEqual(item["validation_status"], "not_run")

    def test_rejected_response_item_needs_operator_fix(self):
        module = _load_module()

        queue = module.build_manual_llm_review_queue(
            ROOT,
            candidates=[_candidate(operator_response_path=str(INVALID_RESPONSE))],
        )

        item = queue["items"][0]
        self.assertTrue(item["response_present"])
        self.assertEqual(item["review_queue_status"], "response_rejected_needs_operator_fix")
        self.assertEqual(item["validation_status"], "rejected")
        self.assertEqual(item["quality_gate_status"], "quality_failed")

    def test_missing_packet_item_is_blocked_missing_packet(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_packet = Path(temp_dir) / "missing_packet.json"

            queue = module.build_manual_llm_review_queue(
                ROOT,
                candidates=[_candidate(packet_path=str(missing_packet))],
            )

        item = queue["items"][0]
        self.assertFalse(item["packet_present"])
        self.assertEqual(item["review_queue_status"], "blocked_missing_packet")

    def test_invalid_local_artifact_shape_is_blocked_invalid_artifact(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_source = Path(temp_dir) / "invalid_source.json"
            invalid_source.write_text("[]", encoding="utf-8")

            queue = module.build_manual_llm_review_queue(
                ROOT,
                candidates=[
                    _candidate(
                        candidate_id="invalid_source_shape",
                        market_id="222",
                        source_artifact_path=str(invalid_source),
                        packet_path="",
                        prompt_path="",
                        operator_response_path="",
                    )
                ],
            )

        item = queue["items"][0]
        self.assertEqual(item["review_queue_status"], "blocked_invalid_artifact")
        self.assertEqual(item["errors"][0]["code"], "source_artifact_top_level_not_object")

    def test_example_or_demo_only_packet_artifacts_are_not_operator_candidates(self):
        module = _load_module()

        queue = module.build_manual_llm_review_queue(ROOT)
        market_ids = {item["market_id"] for item in queue["items"]}
        skipped_reasons = {
            item["reason"] for item in queue["candidate_discovery"]["skipped_candidates"]
        }

        self.assertNotIn("example-pmbot-llm-007-market", market_ids)
        self.assertIn("example_or_demo_packet_excluded", skipped_reasons)

    def test_output_is_deterministic_and_matches_expected_fixture(self):
        _run_exporter()

        queue = _load_json(QUEUE_JSON)
        expected = _load_json(EXPECTED_JSON)
        stdout_queue = json.loads(_run_exporter().stdout)

        self.assertEqual(queue, expected)
        self.assertEqual(stdout_queue, expected)
        self.assertEqual(_load_json(DOC_RESULT)["queue_status_counts"], queue["queue_status_counts"])
        self.assertTrue(DOC_MD.exists())

    def test_forbidden_terms_fail_when_status_or_action_text_contains_them(self):
        module = _load_module()

        findings = module.forbidden_status_action_findings(
            [
                {
                    "market_id": "1",
                    "review_queue_status": "waiting_for_operator_pasted_response",
                    "next_safe_operator_action": "buy after probability review",
                }
            ]
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["field"], "next_safe_operator_action")
        self.assertIn("buy", findings[0]["terms"])
        self.assertIn("probability", findings[0]["terms"])

    def test_markdown_contains_operator_queue_summary_and_safety_boundary(self):
        module = _load_module()
        queue = module.build_manual_llm_review_queue(ROOT)
        markdown = module.render_markdown(queue)

        self.assertIn("PMBOT Manual LLM Review Queue v1", markdown)
        self.assertIn("Queue Status Counts", markdown)
        self.assertIn("response_accepted_for_operator_review: 1", markdown)
        self.assertIn("market_id: 824952", markdown)
        self.assertIn("ready_for_manual_packet_export: 14", markdown)
        self.assertIn("Safety Boundary", markdown)
        self.assertIn("offline_manual_only: true", markdown)
        self.assertIn("not_truth_source: true", markdown)
        self.assertIn("not_trading_advice: true", markdown)
        self.assertIn("not_execution_authority: true", markdown)

    def test_runner_uses_standard_library_and_no_network_llm_browser_or_runtime_imports(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "pm_bot", "re", "sys"})
        self.assertTrue(
            imports.isdisjoint(
                {
                    "requests",
                    "urllib",
                    "httpx",
                    "socket",
                    "webbrowser",
                    "selenium",
                    "playwright",
                    "openai",
                    "anthropic",
                    "subprocess",
                    "web3",
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
