import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "workbench" / "export_operator_review_pack.py"
PACK_JSON = ROOT / "pm_bot" / "workbench" / "operator_review_pack.v1.json"
PACK_MD = ROOT / "pm_bot" / "workbench" / "operator_review_pack.v1.md"
EXPECTED_JSON = ROOT / "pm_bot" / "workbench" / "expected_operator_review_pack.v1.json"
RESULT = ROOT / "docs" / "PMBOT_WORKBENCH_001_RESULT.json"
LANE_RESULT = ROOT / "docs" / "PMBOT_CODEX_A_ROUND003_RESULT.json"
MANUAL_LLM_REVIEW = ROOT / "pm_bot" / "llm" / "manual_llm_paste_in_review.v1.json"
MANUAL_LLM_QUALITY_GATE = ROOT / "pm_bot" / "llm" / "manual_llm_review_quality_gate.v1.json"
MANUAL_LLM_REVIEW_QUEUE = ROOT / "pm_bot" / "llm" / "manual_llm_review_queue.v1.json"
ACTUAL_MANUAL_LLM_RESPONSE_TRIAL = ROOT / "pm_bot" / "llm" / "actual_manual_llm_response_trial.v1.json"
OPENROUTER_PASSIVE_SURFACE_POINTER = ROOT / "pm_bot" / "workbench" / "openrouter_passive_surface_pointer.v1.json"
OPENROUTER_PASSIVE_SURFACE_POINTER_MD = ROOT / "pm_bot" / "workbench" / "openrouter_passive_surface_pointer.v1.md"
OPENROUTER_REVIEW_DASHBOARD = ROOT / "pm_bot" / "workbench" / "operator_openrouter_review_dashboard.v1.json"
PACKET_COMPLETENESS_GATE = ROOT / "pm_bot" / "llm" / "current_llm_batch_readiness_gate.v1.json"

NEW_JSON_FILES = [
    PACK_JSON,
    EXPECTED_JSON,
    OPENROUTER_PASSIVE_SURFACE_POINTER,
    OPENROUTER_REVIEW_DASHBOARD,
    PACKET_COMPLETENESS_GATE,
    RESULT,
    LANE_RESULT,
]


def _frag(*parts):
    return "".join(parts)


def _run_write():
    return subprocess.run(
        [sys.executable, str(RUNNER), "--write"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _run_json():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown():
    return subprocess.run(
        [sys.executable, str(RUNNER), "--markdown"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_module():
    spec = importlib.util.spec_from_file_location("operator_review_pack_export", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _collect_keys(value):
    keys = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(key)
            keys.update(_collect_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(_collect_keys(item))
    return keys


class OperatorReviewPackExportTests(unittest.TestCase):
    def test_write_exports_pack_markdown_expected_and_result_docs(self):
        result = json.loads(_run_write().stdout)

        self.assertEqual(result["task_id"], "PMBOT-WORKBENCH-001-OPERATOR-REVIEW-PACK-EXPORT")
        self.assertEqual(result["status"], "completed_ready_for_review")
        self.assertEqual(result["required_missing_artifacts"], 0)
        self.assertEqual(result["paper_orders_created"], 0)
        self.assertEqual(result["commands_executed"], 0)
        self.assertEqual(result["network_calls"], 0)
        for path in NEW_JSON_FILES:
            self.assertIsInstance(_load_json(path), dict)
        self.assertTrue(PACK_MD.exists())

    def test_pack_json_matches_expected_fixture_and_default_stdout(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        expected = _load_json(EXPECTED_JSON)
        stdout_pack = json.loads(_run_json().stdout)

        self.assertEqual(pack, expected)
        self.assertEqual(stdout_pack, expected)

    def test_pack_contains_required_sections_and_boundary_statements(self):
        _run_write()
        pack = _load_json(PACK_JSON)

        self.assertEqual(pack["schema_version"], "operator_review_pack.v1")
        self.assertEqual(pack["generated_by"], "pm_bot/workbench/export_operator_review_pack.py")
        self.assertFalse(pack["generated_at_policy"]["wall_clock_time_used"])
        for key in (
            "product_stage_summary",
            "artifact_inventory",
            "paper_audit_summary",
            "portfolio_accounting_summary",
            "paper_019_multi_market_run_series",
            "paper_020_paper_run_series_postmortem",
            "dashboard_state_summary",
            "operator_inbox_summary",
            "manual_llm_review",
            "manual_llm_review_quality_gate",
            "manual_llm_review_queue",
            "actual_manual_llm_response_trial",
            "openrouter_passive_surface",
            "openrouter_review_dashboard",
            "packet_completeness_readiness_gate",
            "quality_warning_summary",
            "warnings",
            "missing_artifacts",
            "safety_flags",
            "forbidden_capabilities",
            "next_safe_manual_actions",
        ):
            self.assertIn(key, pack)

        self.assertIn("not strategy profitability", pack["accounting_only_interpretation_warning"])
        self.assertIn("does not recommend markets", pack["no_recommendations_or_decisions_statement"])
        self.assertEqual(pack["paper_orders_created"], 0)
        self.assertEqual(pack["commands_executed"], 0)
        self.assertEqual(pack["network_calls"], 0)

    def test_quality_warning_summary_surfaces_artifact_health_severity_counts(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        quality_summary = pack["quality_warning_summary"]

        self.assertEqual(quality_summary["quality_report_status"], "health_passed")
        self.assertEqual(quality_summary["quality_report_load_status"], "parsed")
        self.assertEqual(
            quality_summary["total_warnings"],
            quality_summary["blocking_warnings"]
            + quality_summary["action_required_warnings"]
            + quality_summary["review_needed_warnings"]
            + quality_summary["informational_warnings"],
        )
        self.assertEqual(quality_summary["blocking_warnings"], 0)
        self.assertFalse(quality_summary["blocking_warning_detected"])
        self.assertEqual(quality_summary["action_required_warnings"], 0)
        self.assertEqual(quality_summary["review_needed_warnings"], 0)
        self.assertEqual(quality_summary["informational_warnings"], 0)
        self.assertIn("blocking means stop and repair", quality_summary["severity_interpretation"]["blocking"])
        self.assertIn(
            "action_required means review before relying",
            quality_summary["severity_interpretation"]["action_required"],
        )
        self.assertEqual(sum(quality_summary["warnings_by_owner"].values()), quality_summary["total_warnings"])
        self.assertEqual(
            sum(quality_summary["warnings_by_action_type"].values()),
            quality_summary["total_warnings"],
        )
        self.assertEqual(quality_summary["warnings_by_owner"]["fixture"], 0)
        self.assertEqual(quality_summary["warnings_by_action_type"]["fix_required"], 0)
        self.assertEqual(quality_summary["top_action_items"], [])

    def test_inventory_reports_required_sources_and_optional_missing_artifacts(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        inventory = {item["artifact_id"]: item for item in pack["artifact_inventory"]["artifacts"]}

        self.assertEqual(pack["artifact_inventory"]["summary"]["required_missing_artifacts"], 0)
        self.assertTrue(inventory["paper_accounting_reconciliation_audit"]["present"])
        self.assertTrue(inventory["paper_accounting_batch_audit"]["present"])
        self.assertTrue(inventory["paper_019_result"]["present"])
        self.assertTrue(inventory["paper_019_multi_market_run_series"]["present"])
        self.assertTrue(inventory["paper_020_result"]["present"])
        self.assertTrue(inventory["paper_020_paper_run_series_postmortem"]["present"])
        self.assertTrue(inventory["portfolio_audit_state_preview"]["present"])
        self.assertTrue(inventory["manual_command_inbox_review"]["present"])
        self.assertTrue(inventory["manual_llm_review_quality_gate"]["present"])
        self.assertTrue(inventory["manual_llm_review_queue"]["present"])
        self.assertTrue(inventory["actual_manual_llm_response_trial"]["present"])
        self.assertTrue(inventory["openrouter_passive_surface"]["present"])
        self.assertTrue(inventory["packet_completeness_readiness_gate"]["present"])
        self.assertEqual(inventory["paper_019_result"]["parse_status"], "parsed")
        self.assertEqual(inventory["paper_019_multi_market_run_series"]["parse_status"], "parsed")
        self.assertEqual(inventory["paper_020_result"]["parse_status"], "parsed")
        self.assertEqual(inventory["paper_020_paper_run_series_postmortem"]["parse_status"], "parsed")
        self.assertEqual(inventory["paper_accounting_batch_audit"]["parse_status"], "parsed")
        self.assertEqual(inventory["manual_llm_review_quality_gate"]["parse_status"], "parsed")
        self.assertEqual(inventory["manual_llm_review_queue"]["parse_status"], "parsed")
        self.assertEqual(inventory["actual_manual_llm_response_trial"]["parse_status"], "parsed")
        self.assertEqual(inventory["openrouter_passive_surface"]["parse_status"], "parsed")
        self.assertEqual(inventory["packet_completeness_readiness_gate"]["parse_status"], "parsed")
        self.assertEqual(
            inventory["paper_019_multi_market_run_series"]["path"],
            "pm_bot/paper/multi_market_paper_run_series.v1.json",
        )
        self.assertEqual(
            inventory["paper_020_paper_run_series_postmortem"]["path"],
            "pm_bot/paper/paper_run_series_postmortem.v1.json",
        )
        self.assertEqual(
            inventory["paper_accounting_batch_audit"]["path"],
            "pm_bot/paper/paper_accounting_batch_audit.v1.json",
        )
        self.assertEqual(
            inventory["manual_llm_review_queue"]["path"],
            "pm_bot/llm/manual_llm_review_queue.v1.json",
        )
        self.assertEqual(
            inventory["actual_manual_llm_response_trial"]["path"],
            "pm_bot/llm/actual_manual_llm_response_trial.v1.json",
        )
        self.assertEqual(
            inventory["openrouter_passive_surface"]["path"],
            "pm_bot/workbench/openrouter_passive_surface_pointer.v1.json",
        )
        self.assertEqual(
            inventory["packet_completeness_readiness_gate"]["path"],
            "pm_bot/llm/current_llm_batch_readiness_gate.v1.json",
        )

        missing = {item["path"]: item for item in pack["missing_artifacts"]}
        for path in (
            "docs/PMBOT_INFRA_009_RESULT.json",
            "docs/PMBOT_INFRA_009_ABC_ROUND003_WORKTREE_MATERIALIZATION.md",
        ):
            if not (ROOT / path).exists():
                self.assertIn(path, missing)
                self.assertFalse(missing[path]["required"])
        self.assertTrue(all(not item["required"] for item in pack["missing_artifacts"]))

    def test_audit_dashboard_portfolio_and_inbox_summaries_are_explicit(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        paper = pack["paper_audit_summary"]
        portfolio = pack["portfolio_accounting_summary"]
        dashboard = pack["dashboard_state_summary"]
        inbox = pack["operator_inbox_summary"]

        self.assertEqual(paper["reconciliation_audit"]["audit_status"], "reconciliation_passed")
        self.assertEqual(paper["reconciliation_audit"]["counts"]["checks_failed"], 0)
        self.assertEqual(paper["batch_audit"]["audit_status"], "batch_audit_passed")
        self.assertEqual(paper["batch_audit"]["counts"]["records_audited"], 3)
        self.assertEqual(paper["batch_audit"]["counts"]["checks_failed"], 0)
        self.assertEqual(
            paper["audits_passed"],
            [
                {
                    "artifact_id": "paper_accounting_reconciliation_audit",
                    "audit_status": "reconciliation_passed",
                },
                {
                    "artifact_id": "paper_accounting_batch_audit",
                    "audit_status": "batch_audit_passed",
                },
            ],
        )

        self.assertEqual(portfolio["summary_status"], "portfolio_accounting_state_ready")
        self.assertEqual(portfolio["accepted_accounting_market_ids"], ["824952"])
        self.assertTrue(portfolio["interpretation_boundary"]["paper_accounting_only"])
        self.assertFalse(portfolio["interpretation_boundary"]["strategy_profitability"])
        self.assertEqual(dashboard["schema_version"], "portfolio_audit_state_preview.v1")
        self.assertFalse(dashboard["implementation_boundary"]["runtime_wiring"])
        self.assertEqual(inbox["records_seen"], 7)
        self.assertEqual(inbox["accepted_count"], 3)
        self.assertEqual(inbox["rejected_count"], 3)
        self.assertEqual(inbox["needs_human_review_count"], 1)
        self.assertFalse(inbox["execution_authority"])
        self.assertEqual(inbox["commands_executed"], 0)

    def test_manual_llm_review_section_surfaces_present_artifact_status_only(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        source = _load_json(MANUAL_LLM_REVIEW)
        manual_llm = pack["manual_llm_review"]

        self.assertEqual(manual_llm["section_id"], "manual_llm_review")
        self.assertEqual(manual_llm["artifact_status"], "present")
        self.assertEqual(
            manual_llm["artifact_pointer"],
            "pm_bot/llm/manual_llm_paste_in_review.v1.json",
        )
        self.assertEqual(manual_llm["artifact_parse_status"], "parsed")
        self.assertEqual(manual_llm["validation_status"], source["validation_status"])
        self.assertEqual(manual_llm["errors_count"], len(source["errors"]))
        self.assertEqual(manual_llm["warnings_count"], len(source["warnings"]))
        self.assertEqual(manual_llm["accepted_sections"], source["accepted_sections"])
        self.assertEqual(manual_llm["missing_sections"], source["missing_sections"])
        self.assertEqual(
            manual_llm["forbidden_content_detected"],
            {
                "detected": source["forbidden_content_detected"]["detected"],
                "findings_count": len(source["forbidden_content_detected"]["findings"]),
            },
        )
        self.assertEqual(manual_llm["next_safe_operator_action"], source["next_safe_operator_action"])
        self.assertIn("analysis-only and not trading advice", manual_llm["analysis_only_warning"])
        self.assertFalse(manual_llm["llm_text_generated"])
        self.assertFalse(manual_llm["llm_api_calls_added"])
        self.assertFalse(manual_llm["browser_automation_added"])
        self.assertFalse(manual_llm["runtime_integration_added"])

    def test_manual_llm_quality_gate_section_surfaces_present_artifact_status_only(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        source = _load_json(MANUAL_LLM_QUALITY_GATE)
        quality_gate = pack["manual_llm_review_quality_gate"]

        self.assertEqual(quality_gate["section_id"], "manual_llm_review_quality_gate")
        self.assertEqual(quality_gate["artifact_status"], "present")
        self.assertEqual(
            quality_gate["artifact_pointer"],
            "pm_bot/llm/manual_llm_review_quality_gate.v1.json",
        )
        self.assertEqual(quality_gate["artifact_parse_status"], "parsed")
        self.assertEqual(quality_gate["validation_status"], source["validation_status"])
        self.assertEqual(quality_gate["base_validator_status"], source["base_validator_status"])
        self.assertEqual(quality_gate["quality_counts"]["checks_total"], source["quality_counts"]["checks_total"])
        self.assertEqual(quality_gate["quality_counts"]["errors_count"], source["quality_counts"]["errors_count"])
        self.assertEqual(quality_gate["quality_counts"]["warnings_count"], source["quality_counts"]["warnings_count"])
        self.assertEqual(
            quality_gate["required_sections_check"]["status"],
            source["required_sections_check"]["status"],
        )
        self.assertEqual(
            quality_gate["minimum_content_check"]["status"],
            source["minimum_content_check"]["status"],
        )
        self.assertEqual(
            quality_gate["generic_or_placeholder_text_check"]["status"],
            source["generic_or_placeholder_text_check"]["status"],
        )
        self.assertEqual(
            quality_gate["unsafe_certainty_check"]["status"],
            source["unsafe_certainty_check"]["status"],
        )
        self.assertEqual(
            quality_gate["forbidden_content_check"]["status"],
            source["forbidden_content_check"]["status"],
        )
        self.assertEqual(quality_gate["next_safe_operator_action"], source["next_safe_operator_action"])
        self.assertIn("deterministic offline quality gate only", quality_gate["deterministic_quality_gate_warning"])
        self.assertIn("not truth evaluation", quality_gate["deterministic_quality_gate_warning"])
        self.assertIn("probability, EV, edge, side, or trading advice", quality_gate["deterministic_quality_gate_warning"])
        self.assertFalse(quality_gate["llm_text_generated"])
        self.assertFalse(quality_gate["llm_api_calls_added"])
        self.assertFalse(quality_gate["browser_automation_added"])
        self.assertFalse(quality_gate["runtime_integration_added"])

    def test_manual_llm_review_queue_section_surfaces_passive_queue_status_only(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        source = _load_json(MANUAL_LLM_REVIEW_QUEUE)
        queue = pack["manual_llm_review_queue"]

        self.assertEqual(queue["section_id"], "manual_llm_review_queue")
        self.assertEqual(queue["artifact_status"], "present")
        self.assertEqual(queue["artifact_pointer"], "pm_bot/llm/manual_llm_review_queue.v1.json")
        self.assertEqual(queue["parse_status"], "parsed")
        self.assertEqual(queue["queue_items_total"], source["queue_items_total"])
        self.assertEqual(queue["queue_status_counts"], source["queue_status_counts"])
        self.assertEqual(queue["additional_ready_candidates_found"], 14)
        self.assertEqual(queue["errors_count"], len(source["errors"]))
        self.assertEqual(queue["warnings_count"], len(source["warnings"]))
        accepted_item = next(item for item in queue["items"] if item["market_id"] == "824952")
        self.assertEqual(accepted_item["market_id"], "824952")
        self.assertEqual(
            accepted_item["review_queue_status"],
            "response_accepted_for_operator_review",
        )
        self.assertTrue(accepted_item["response_present"])
        self.assertTrue(queue["offline_manual_only"])
        self.assertTrue(queue["not_truth_source"])
        self.assertTrue(queue["not_trading_advice"])
        self.assertTrue(queue["not_execution_authority"])
        self.assertFalse(queue["llm_api_calls_added"])
        self.assertFalse(queue["browser_automation_added"])
        self.assertFalse(queue["runtime_integration_added"])
        self.assertFalse(queue["prompt_automation_added"])

    def test_actual_manual_llm_response_trial_section_surfaces_accepted_artifact_status_only(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        source = _load_json(ACTUAL_MANUAL_LLM_RESPONSE_TRIAL)
        trial = pack["actual_manual_llm_response_trial"]

        self.assertEqual(trial["section_id"], "actual_manual_llm_response_trial")
        self.assertEqual(trial["contract_version"], "actual_manual_llm_response_workbench_surface.v1")
        self.assertEqual(trial["artifact_status"], "present")
        self.assertEqual(trial["artifact_path"], "pm_bot/llm/actual_manual_llm_response_trial.v1.json")
        self.assertTrue(trial["artifact_present"])
        self.assertEqual(trial["parse_status"], "parsed")
        self.assertEqual(
            trial["operator_response_path"],
            "pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json",
        )
        self.assertTrue(trial["operator_response_present"])
        self.assertTrue(trial["trial_artifact_operator_response_present"])
        self.assertEqual(trial["market_id"], source["market_id"])
        self.assertEqual(trial["source_artifact_path"], source["source_artifact_path"])
        self.assertEqual(trial["response_source_type"], source["response_source_type"])
        self.assertEqual(trial["trial_packet_source_type"], source["trial_packet_source_type"])
        self.assertEqual(trial["run_status"], source["run_status"])
        self.assertEqual(trial["acceptance_status"], source["acceptance_status"])
        self.assertEqual(trial["response_validation_status"], source["response_validation_status"])
        self.assertEqual(trial["manual_review_status"], source["manual_review_status"])
        self.assertEqual(trial["quality_gate_status"], source["quality_gate_status"])
        self.assertEqual(trial["errors_count"], len(source["errors"]))
        self.assertEqual(trial["warnings_count"], len(source["warnings"]))
        self.assertEqual(trial["next_safe_operator_action"], source["next_safe_operator_action"])
        self.assertTrue(trial["offline_review_context_only"])
        self.assertTrue(trial["not_truth_source"])
        self.assertTrue(trial["not_trading_advice"])
        self.assertTrue(trial["not_execution_authority"])
        self.assertFalse(trial["llm_text_generated"])
        self.assertFalse(trial["llm_api_calls_added"])
        self.assertFalse(trial["browser_automation_added"])
        self.assertFalse(trial["runtime_integration_added"])
        self.assertIn("offline review context only", trial["explicit_operator_warning"])

    def test_openrouter_passive_surface_section_surfaces_pointer_only(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        pointer = _load_json(OPENROUTER_PASSIVE_SURFACE_POINTER)
        section = pack["openrouter_passive_surface"]

        self.assertTrue(OPENROUTER_PASSIVE_SURFACE_POINTER_MD.exists())
        self.assertEqual(section["section_id"], "openrouter_passive_surface")
        self.assertEqual(section["artifact_status"], "present")
        self.assertEqual(
            section["artifact_pointer"],
            "pm_bot/workbench/openrouter_passive_surface_pointer.v1.json",
        )
        self.assertEqual(section["artifact_parse_status"], "parsed")
        self.assertEqual(section["source_batch_task"], "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL")
        self.assertEqual(
            section["source_baseline_task"],
            "PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY",
        )
        self.assertEqual(
            section["source_surface_task"],
            "PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-AND-WORKBENCH-N5-INTEGRATION",
        )
        self.assertEqual(section["source_048_status"], "completed_pushed")
        self.assertEqual(section["source_052_status"], "completed_pushed")
        self.assertEqual(section["surfaced_market_ids"], ["569344", "569366", "569368", "569373", "573656"])
        self.assertEqual(section["model"], "anthropic/claude-sonnet-4.5")
        self.assertEqual(section["total_calls"], 5)
        self.assertEqual(section["aggregate_usage"], pointer["aggregate_usage"])
        self.assertEqual(section["aggregate_cost"], pointer["aggregate_cost"])
        self.assertEqual(section["normalization_summary"], pointer["normalization_summary"])
        self.assertEqual(section["quality_summary"], pointer["quality_summary"])
        self.assertEqual(len(section["surface_history"]), 2)
        self.assertEqual(section["combined_openrouter_review_contour_summary"]["combined_tokens"], 48573)
        self.assertEqual(pack["openrouter_review_dashboard"]["artifact_status"], "present")
        self.assertEqual(pack["openrouter_review_dashboard"]["inventory_summary"]["total_markets_found"], 14)
        for flag in (
            "operator_review_only",
            "passive_context_only",
            "no_trading_authority",
            "no_queue_authority",
            "no_runtime_authority",
            "no_dispatcher_authority",
            "no_wallet_or_order_authority",
            "acceptance_is_not_trading_approval",
            "analysis_only",
            "manual_review_only",
        ):
            self.assertTrue(section["safety_summary"][flag])

        self.assertFalse(section["safety_summary"]["raw_model_responses_included"])
        self.assertFalse(section["safety_summary"]["per_market_response_text_included"])
        self.assertFalse(section["safety_summary"]["runtime_wiring_added"])
        self.assertFalse(section["safety_summary"]["dispatcher_changes_added"])
        self.assertFalse(section["safety_summary"]["background_workers_added"])
        self.assertFalse(section["safety_summary"]["queue_items_created"])
        self.assertFalse(section["safety_summary"]["queue_state_mutated"])
        self.assertFalse(section["safety_summary"]["browser_automation_added"])
        self.assertFalse(section["safety_summary"]["wallet_or_order_access_added"])
        self.assertEqual(section["safety_summary"]["openrouter_calls_performed"], 0)
        self.assertEqual(section["safety_summary"]["polymarket_api_calls_performed"], 0)
        self.assertEqual(section["safety_summary"]["network_calls"], 0)
        self.assertEqual(section["safety_summary"]["orders_created"], 0)
        self.assertNotIn("per_market_passive_entries", section)
        for item in section["artifact_pointers"].values():
            self.assertTrue((ROOT / item["path"]).exists())

    def test_openrouter_passive_surface_missing_pointer_is_non_blocking(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as directory:
            pack = module.build_operator_review_pack(Path(directory))

        section = pack["openrouter_passive_surface"]
        warnings = {item["warning_id"]: item for item in pack["warnings"]}
        self.assertEqual(section["artifact_status"], "missing")
        self.assertEqual(
            section["artifact_pointer"],
            "pm_bot/workbench/openrouter_passive_surface_pointer.v1.json",
        )
        self.assertEqual(section["source_batch_task"], "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL")
        self.assertEqual(
            section["source_baseline_task"],
            "PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY",
        )
        self.assertEqual(
            section["source_surface_task"],
            "PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-AND-WORKBENCH-N5-INTEGRATION",
        )
        self.assertEqual(section["surfaced_market_ids"], [])
        self.assertEqual(section["total_calls"], 0)
        self.assertIn("openrouter_passive_surface_pointer_missing", warnings)
        self.assertEqual(section["safety_summary"]["openrouter_calls_performed"], 0)
        self.assertEqual(section["safety_summary"]["polymarket_api_calls_performed"], 0)
        self.assertFalse(section["safety_summary"]["queue_items_created"])

    def test_manual_llm_review_missing_artifact_is_not_available_and_non_blocking(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as directory:
            pack = module.build_operator_review_pack(Path(directory))

        manual_llm = pack["manual_llm_review"]
        self.assertEqual(manual_llm["artifact_status"], "missing")
        self.assertEqual(manual_llm["validation_status"], "not_available")
        self.assertEqual(manual_llm["accepted_sections"], [])
        self.assertEqual(manual_llm["missing_sections"], [])
        self.assertFalse(manual_llm["forbidden_content_detected"]["detected"])
        self.assertIn("not available locally", manual_llm["safe_error_summary"][0])
        self.assertFalse(manual_llm["llm_text_generated"])

    def test_manual_llm_review_malformed_artifact_is_invalid_and_non_blocking(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            review_path = temp_root / "pm_bot" / "llm" / "manual_llm_paste_in_review.v1.json"
            review_path.parent.mkdir(parents=True, exist_ok=True)
            review_path.write_text("{", encoding="utf-8")

            pack = module.build_operator_review_pack(temp_root)

        manual_llm = pack["manual_llm_review"]
        self.assertEqual(manual_llm["artifact_status"], "invalid")
        self.assertEqual(manual_llm["validation_status"], "rejected_or_unreadable")
        self.assertEqual(manual_llm["artifact_parse_status"], "parse_failed")
        self.assertEqual(manual_llm["accepted_sections"], [])
        self.assertEqual(manual_llm["missing_sections"], [])
        self.assertIn("could not be read safely", manual_llm["safe_error_summary"][0])
        self.assertFalse(manual_llm["llm_text_generated"])

    def test_manual_llm_quality_gate_missing_artifact_is_not_available_and_non_blocking(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as directory:
            pack = module.build_operator_review_pack(Path(directory))

        quality_gate = pack["manual_llm_review_quality_gate"]
        self.assertEqual(quality_gate["artifact_status"], "missing")
        self.assertEqual(quality_gate["validation_status"], "not_available")
        self.assertEqual(quality_gate["base_validator_status"], "not_available")
        self.assertEqual(quality_gate["quality_counts"]["checks_total"], 0)
        self.assertEqual(quality_gate["required_sections_check"]["status"], "not_available")
        self.assertIn("not available locally", quality_gate["safe_error_summary"][0])
        self.assertFalse(quality_gate["llm_text_generated"])

    def test_manual_llm_quality_gate_malformed_artifact_is_invalid_and_non_blocking(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            quality_gate_path = temp_root / "pm_bot" / "llm" / "manual_llm_review_quality_gate.v1.json"
            quality_gate_path.parent.mkdir(parents=True, exist_ok=True)
            quality_gate_path.write_text("{", encoding="utf-8")

            pack = module.build_operator_review_pack(temp_root)

        quality_gate = pack["manual_llm_review_quality_gate"]
        self.assertEqual(quality_gate["artifact_status"], "invalid")
        self.assertEqual(quality_gate["validation_status"], "rejected_or_unreadable")
        self.assertEqual(quality_gate["artifact_parse_status"], "parse_failed")
        self.assertEqual(quality_gate["base_validator_status"], "not_available")
        self.assertEqual(quality_gate["quality_counts"]["checks_total"], 0)
        self.assertIn("could not be read safely", quality_gate["safe_error_summary"][0])
        self.assertFalse(quality_gate["llm_text_generated"])

    def test_actual_manual_llm_response_trial_missing_artifact_is_not_available_and_non_blocking(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as directory:
            pack = module.build_operator_review_pack(Path(directory))

        trial = pack["actual_manual_llm_response_trial"]
        warnings = {item["warning_id"]: item for item in pack["warnings"]}
        self.assertEqual(trial["artifact_status"], "missing")
        self.assertFalse(trial["artifact_present"])
        self.assertEqual(trial["parse_status"], "missing")
        self.assertEqual(trial["run_status"], "not_available")
        self.assertEqual(trial["acceptance_status"], "not_available")
        self.assertIn("not available locally", trial["safe_error_summary"][0])
        self.assertIn("actual_manual_llm_response_trial_missing", warnings)
        self.assertTrue(trial["offline_review_context_only"])

    def test_actual_manual_llm_response_trial_malformed_artifact_is_invalid_and_non_blocking(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            trial_path = temp_root / "pm_bot" / "llm" / "actual_manual_llm_response_trial.v1.json"
            trial_path.parent.mkdir(parents=True, exist_ok=True)
            trial_path.write_text("{", encoding="utf-8")

            pack = module.build_operator_review_pack(temp_root)

        trial = pack["actual_manual_llm_response_trial"]
        warnings = {item["warning_id"]: item for item in pack["warnings"]}
        self.assertEqual(trial["artifact_status"], "invalid")
        self.assertTrue(trial["artifact_present"])
        self.assertEqual(trial["parse_status"], "parse_failed")
        self.assertEqual(trial["run_status"], "not_available")
        self.assertIn("could not be read safely", trial["safe_error_summary"][0])
        self.assertIn("actual_manual_llm_response_trial_invalid", warnings)
        self.assertFalse(trial["llm_text_generated"])

    def test_manual_llm_review_surface_does_not_generate_llm_text_or_forbidden_fields(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        manual_llm = pack["manual_llm_review"]
        quality_gate = pack["manual_llm_review_quality_gate"]
        keys = _collect_keys(manual_llm)
        quality_gate_keys = _collect_keys(quality_gate)

        self.assertNotIn("operator_summary", manual_llm)
        self.assertNotIn("packet_validation", manual_llm)
        self.assertNotIn("response_validation", manual_llm)
        self.assertNotIn("source_artifacts", manual_llm)
        self.assertNotIn("operator_summary", quality_gate)
        self.assertNotIn("packet_validation", quality_gate)
        self.assertNotIn("response_validation", quality_gate)
        self.assertNotIn("source_artifacts", quality_gate)
        self.assertFalse(manual_llm["llm_text_generated"])
        self.assertFalse(quality_gate["llm_text_generated"])
        for forbidden_field in (
            "probability",
            "ev",
            "edge",
            "score",
            "scoring",
            "recommended_side",
            "side_recommendation",
            "side_recommendations",
            "truth_evaluation",
        ):
            self.assertNotIn(forbidden_field, keys)
            self.assertNotIn(forbidden_field, quality_gate_keys)

    def test_manual_llm_review_surface_adds_no_network_llm_browser_or_runtime_calls(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        manual_llm = pack["manual_llm_review"]
        quality_gate = pack["manual_llm_review_quality_gate"]
        queue = pack["manual_llm_review_queue"]
        actual_trial = pack["actual_manual_llm_response_trial"]
        openrouter = pack["openrouter_passive_surface"]

        self.assertFalse(manual_llm["llm_api_calls_added"])
        self.assertFalse(manual_llm["browser_automation_added"])
        self.assertFalse(manual_llm["runtime_integration_added"])
        self.assertFalse(quality_gate["llm_api_calls_added"])
        self.assertFalse(quality_gate["browser_automation_added"])
        self.assertFalse(quality_gate["runtime_integration_added"])
        self.assertFalse(queue["llm_api_calls_added"])
        self.assertFalse(queue["browser_automation_added"])
        self.assertFalse(queue["runtime_integration_added"])
        self.assertFalse(queue["prompt_automation_added"])
        self.assertFalse(actual_trial["llm_api_calls_added"])
        self.assertFalse(actual_trial["browser_automation_added"])
        self.assertFalse(actual_trial["runtime_integration_added"])
        self.assertEqual(openrouter["safety_summary"]["openrouter_calls_performed"], 0)
        self.assertEqual(openrouter["safety_summary"]["polymarket_api_calls_performed"], 0)
        self.assertFalse(openrouter["safety_summary"]["browser_automation_added"])
        self.assertFalse(openrouter["safety_summary"]["runtime_wiring_added"])
        self.assertFalse(openrouter["safety_summary"]["dispatcher_changes_added"])
        self.assertFalse(openrouter["safety_summary"]["queue_items_created"])
        self.assertFalse(openrouter["safety_summary"]["queue_state_mutated"])
        self.assertEqual(pack["network_calls"], 0)
        self.assertEqual(pack["commands_executed"], 0)
        self.assertEqual(pack["paper_orders_created"], 0)

    def test_paper_019_multi_market_run_series_summary_is_visible_and_accounting_only(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        paper_019 = pack["paper_019_multi_market_run_series"]

        self.assertEqual(paper_019["section_id"], "paper_019_multi_market_run_series")
        self.assertEqual(paper_019["artifact_status"], "present")
        self.assertEqual(
            paper_019["artifact_pointer"],
            "pm_bot/paper/multi_market_paper_run_series.v1.json",
        )
        self.assertEqual(paper_019["artifact_parse_status"], "parsed")
        self.assertEqual(paper_019["series_status"], "series_run_passed")
        self.assertEqual(paper_019["markets_seen"], 5)
        self.assertEqual(paper_019["records_seen"], 5)
        self.assertEqual(paper_019["records_processed"], 4)
        self.assertEqual(
            paper_019["records_by_status"],
            {
                "accepted_accounting_record": 3,
                "blocked_fixture_record": 1,
                "manual_review_only": 1,
            },
        )
        self.assertEqual(
            paper_019["accounting_summary"]["paper_accounting_cumulative_pnl"],
            "-1.00",
        )
        self.assertEqual(
            paper_019["accounting_summary"]["paper_accounting_average_settled_pnl"],
            "-0.33",
        )

        blocked_manual = paper_019["blocked_or_manual_review_summary"]
        self.assertEqual(blocked_manual["blocked_fixture_record_count"], 1)
        self.assertEqual(blocked_manual["manual_review_only_count"], 1)
        self.assertEqual(blocked_manual["blocked_or_rejected_records"], 1)
        self.assertEqual(blocked_manual["manual_review_only_records"], 1)
        self.assertEqual(
            [record["processing_status"] for record in blocked_manual["records"]],
            ["manual_review_only", "blocked_fixture_record"],
        )
        self.assertIn(
            "fixture/accounting-only outputs",
            paper_019["interpretation_warning"],
        )
        self.assertIn("not strategy profitability", paper_019["interpretation_warning"])
        self.assertIn("recommendation, EV, edge, probability", paper_019["interpretation_warning"])
        self.assertEqual(
            paper_019["safety_counters"],
            {
                "real_orders_created": 0,
                "autonomous_paper_orders": 0,
                "network_calls": 0,
                "commands_executed": 0,
                "autonomous_decisions": 0,
            },
        )

    def test_paper_020_postmortem_summary_is_visible_and_accounting_only(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        paper_020 = pack["paper_020_paper_run_series_postmortem"]

        self.assertEqual(paper_020["section_id"], "paper_020_paper_run_series_postmortem")
        self.assertEqual(paper_020["artifact_status"], "present")
        self.assertEqual(
            paper_020["artifact_pointer"],
            "pm_bot/paper/paper_run_series_postmortem.v1.json",
        )
        self.assertEqual(paper_020["artifact_parse_status"], "parsed")
        self.assertEqual(paper_020["postmortem_status"], "postmortem_completed")
        self.assertTrue(paper_020["source_paper_019_found"])
        self.assertEqual(paper_020["source_paper_019"]["series_status"], "series_run_passed")
        self.assertEqual(paper_020["source_paper_019"]["markets_seen"], 5)
        self.assertEqual(paper_020["source_paper_019"]["records_seen"], 5)
        self.assertEqual(paper_020["source_paper_019"]["records_processed"], 4)
        self.assertEqual(paper_020["cumulative_pnl"], "-1.00")
        self.assertTrue(paper_020["accounting_only_warning_present"])
        self.assertIn("not strategy profitability", paper_020["accounting_only_warning"])
        self.assertIn("EV, probability estimate", paper_020["accounting_only_warning"])
        self.assertEqual(
            paper_020["records_by_status"],
            {
                "accepted_accounting_record": 3,
                "blocked_fixture_record": 1,
                "manual_review_only": 1,
            },
        )
        self.assertEqual(
            [item["processing_status"] for item in paper_020["record_status_notes"]],
            ["accepted_accounting_record", "manual_review_only", "blocked_fixture_record"],
        )
        self.assertGreaterEqual(len(paper_020["fixture_limitations"]), 5)
        self.assertGreaterEqual(len(paper_020["recommended_next_fixture_expansions"]), 4)
        self.assertEqual(
            paper_020["safety_counters"],
            {
                "real_orders_created": 0,
                "autonomous_paper_orders": 0,
                "network_calls": 0,
                "commands_executed": 0,
                "autonomous_decisions": 0,
            },
        )
        self.assertEqual(
            paper_020["next_safe_action"],
            "PMBOT-WORKBENCH-006-SURFACE-PAPER-020-POSTMORTEM or PMBOT-PRODUCT-002-NEXT-MVP-GATE-REVIEW",
        )

    def test_paper_019_missing_artifact_remains_non_blocking_warning(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as directory:
            pack = module.build_operator_review_pack(Path(directory))

        paper_019 = pack["paper_019_multi_market_run_series"]
        paper_020 = pack["paper_020_paper_run_series_postmortem"]
        warnings = {item["warning_id"]: item for item in pack["warnings"]}

        self.assertEqual(paper_019["artifact_status"], "missing")
        self.assertEqual(paper_019["artifact_pointer"], "pm_bot/paper/multi_market_paper_run_series.v1.json")
        self.assertEqual(paper_019["markets_seen"], 0)
        self.assertEqual(paper_019["records_seen"], 0)
        self.assertEqual(paper_019["records_processed"], 0)
        self.assertEqual(paper_019["records_by_status"], {})
        self.assertEqual(paper_019["accounting_summary"], {})
        self.assertEqual(paper_019["blocked_or_manual_review_summary"]["records"], [])
        self.assertEqual(paper_019["safety_counters"]["network_calls"], 0)
        self.assertIn("paper_019_multi_market_run_series_missing", warnings)
        self.assertEqual(
            warnings["paper_019_multi_market_run_series_missing"]["category"],
            "optional_artifact_missing",
        )
        self.assertEqual(paper_020["artifact_status"], "missing")
        self.assertEqual(paper_020["artifact_pointer"], "pm_bot/paper/paper_run_series_postmortem.v1.json")
        self.assertFalse(paper_020["source_paper_019_found"])
        self.assertEqual(paper_020["source_paper_019"]["markets_seen"], 0)
        self.assertEqual(paper_020["source_paper_019"]["records_seen"], 0)
        self.assertEqual(paper_020["source_paper_019"]["records_processed"], 0)
        self.assertEqual(paper_020["records_by_status"], {})
        self.assertEqual(paper_020["safety_counters"]["network_calls"], 0)
        self.assertIn("paper_020_paper_run_series_postmortem_missing", warnings)
        self.assertEqual(
            warnings["paper_020_paper_run_series_postmortem_missing"]["category"],
            "optional_artifact_missing",
        )

    def test_warnings_safety_flags_and_next_actions_remain_review_only(self):
        _run_write()
        pack = _load_json(PACK_JSON)
        warnings = {item["warning_id"]: item["message"] for item in pack["warnings"]}
        safety = pack["safety_flags"]

        self.assertIn("accounting_only_interpretation", warnings)
        self.assertIn("no_recommendations_or_decisions", warnings)
        self.assertIn("local artifacts only", warnings["local_artifacts_only"])
        self.assertTrue(safety["operator_review_only"])
        self.assertTrue(safety["local_file_reads_only"])
        self.assertFalse(safety["runtime_wiring"])
        self.assertFalse(safety["network_api"])
        self.assertFalse(safety["wallet"])
        self.assertFalse(safety["trading"])
        self.assertFalse(safety["autonomous_paper_orders"])
        self.assertFalse(safety["scoring_probability_ev_edge"])
        self.assertFalse(safety["market_decisions"])
        self.assertFalse(safety["command_execution"])
        self.assertTrue(all(action["non_trading_action"] for action in pack["next_safe_manual_actions"]))
        self.assertTrue(all(not action["requires_runtime"] for action in pack["next_safe_manual_actions"]))
        self.assertTrue(all(not action["creates_orders"] for action in pack["next_safe_manual_actions"]))

    def test_markdown_matches_cli_output(self):
        _run_write()
        markdown = PACK_MD.read_text(encoding="utf-8")

        self.assertEqual(_run_markdown().stdout, markdown)
        self.assertIn("PMBOT Operator Review Pack v1", markdown)
        self.assertIn("paper_orders_created: 0", markdown)
        self.assertIn("commands_executed: 0", markdown)
        self.assertIn("network_calls: 0", markdown)
        self.assertIn("Quality Warning Summary", markdown)
        self.assertIn("blocking means stop and repair", markdown)
        self.assertIn("PAPER-019 Multi-Market Run Series", markdown)
        self.assertIn("section_id: paper_019_multi_market_run_series", markdown)
        self.assertIn("markets_seen: 5", markdown)
        self.assertIn("paper_accounting_cumulative_pnl: -1.00", markdown)
        self.assertIn("PAPER-019 values are deterministic fixture/accounting-only outputs", markdown)
        self.assertIn("PAPER-020 Paper Run Series Postmortem", markdown)
        self.assertIn("section_id: paper_020_paper_run_series_postmortem", markdown)
        self.assertIn("postmortem_status: postmortem_completed", markdown)
        self.assertIn("source_paper_019_found: true", markdown)
        self.assertIn("cumulative_pnl: -1.00", markdown)
        self.assertIn("PAPER-019 PnL is accounting-only fixture output", markdown)
        self.assertIn("PAPER-020 Fixture Limitations", markdown)
        self.assertIn("PAPER-020 Recommended Next Fixture Expansions", markdown)
        self.assertIn("autonomous_paper_orders: 0", markdown)
        self.assertIn("Paper accounting PnL is fixture/manual accounting only", markdown)
        self.assertIn("does not recommend markets", markdown)
        self.assertIn("Manual LLM Review", markdown)
        self.assertIn("artifact_status: present", markdown)
        self.assertIn("validation_status: accepted", markdown)
        self.assertIn("analysis-only and not trading advice", markdown)
        self.assertIn("llm_text_generated: false", markdown)
        self.assertIn("Manual LLM Review Quality Gate", markdown)
        self.assertIn("artifact_pointer: pm_bot/llm/manual_llm_review_quality_gate.v1.json", markdown)
        self.assertIn("validation_status: quality_passed", markdown)
        self.assertIn("base_validator_status: accepted", markdown)
        self.assertIn("Manual LLM Quality Gate Check Summaries", markdown)
        self.assertIn("required_sections_check: status=passed", markdown)
        self.assertIn("minimum_content_check: status=passed", markdown)
        self.assertIn("generic_or_placeholder_text_check: status=passed", markdown)
        self.assertIn("unsafe_certainty_check: status=passed", markdown)
        self.assertIn("forbidden_content_check: status=passed", markdown)
        self.assertIn("deterministic offline quality gate only", markdown)
        self.assertIn("not truth evaluation, probability, EV, edge, side, or trading advice", markdown)
        self.assertIn("Manual LLM Review Queue", markdown)
        self.assertIn("artifact_pointer: pm_bot/llm/manual_llm_review_queue.v1.json", markdown)
        self.assertIn("queue_items_total: 15", markdown)
        self.assertIn("ready_for_manual_packet_export: 0", markdown)
        self.assertIn("waiting_for_operator_pasted_response: 14", markdown)
        self.assertIn("response_accepted_for_operator_review: 1", markdown)
        self.assertIn("offline_manual_only: true", markdown)
        self.assertIn("Actual Manual LLM Response Trial", markdown)
        self.assertIn("artifact_path: pm_bot/llm/actual_manual_llm_response_trial.v1.json", markdown)
        self.assertIn("operator_response_present: true", markdown)
        self.assertIn("response_source_type: actual_operator_pasted_response", markdown)
        self.assertIn("market_id: 824952", markdown)
        self.assertIn("run_status: actual_response_accepted", markdown)
        self.assertIn("acceptance_status: accepted_for_operator_review", markdown)
        self.assertIn("response_validation_status: accepted", markdown)
        self.assertIn("manual_review_status: accepted", markdown)
        self.assertIn("quality_gate_status: quality_passed", markdown)
        self.assertIn("offline_review_context_only: true", markdown)
        self.assertIn("not_truth_source: true", markdown)
        self.assertIn("not_trading_advice: true", markdown)
        self.assertIn("not_execution_authority: true", markdown)
        self.assertIn("not a truth source, not trading advice, and not execution authority", markdown)
        self.assertIn("OpenRouter Passive Surface", markdown)
        self.assertIn("section_id: openrouter_passive_surface", markdown)
        self.assertIn("artifact_pointer: pm_bot/workbench/openrouter_passive_surface_pointer.v1.json", markdown)
        self.assertIn("source_batch_task: PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL", markdown)
        self.assertIn(
            "source_baseline_task: PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY",
            markdown,
        )
        self.assertIn(
            "source_surface_task: PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-AND-WORKBENCH-N5-INTEGRATION",
            markdown,
        )
        self.assertIn("source_048_status: completed_pushed", markdown)
        self.assertIn("source_052_status: completed_pushed", markdown)
        self.assertIn("surfaced_market_ids: 569344, 569366, 569368, 569373, 573656", markdown)
        self.assertIn("model: anthropic/claude-sonnet-4.5", markdown)
        self.assertIn("total_calls: 5", markdown)
        self.assertIn("prompt_tokens: 20768", markdown)
        self.assertIn("completion_tokens: 9119", markdown)
        self.assertIn("total_tokens: 29887", markdown)
        self.assertIn("fenced_response_count: 5", markdown)
        self.assertIn("clean_raw_json_response_count: 0", markdown)
        self.assertIn("OpenRouter Passive Surface History", markdown)
        self.assertIn("N=3: calls=3", markdown)
        self.assertIn("N=5: calls=5", markdown)
        self.assertIn("OpenRouter Combined Review Contour", markdown)
        self.assertIn("combined_cost: 0.325071", markdown)
        self.assertIn("Packet Completeness Readiness Gate", markdown)
        self.assertIn("artifact_pointer: pm_bot/llm/current_llm_batch_readiness_gate.v1.json", markdown)
        self.assertIn("low_readiness_market_ids: 597964, 598936, 691547, 692258", markdown)
        self.assertIn("future_openrouter_batch_approved: false", markdown)
        self.assertIn("OpenRouter Review Dashboard", markdown)
        self.assertIn("total_markets_found: 14", markdown)
        self.assertIn("evidence_readiness_integration_status: source_001_context_ready", markdown)
        self.assertIn("evidence_readiness_low_count: 4", markdown)
        self.assertIn("average_evidence_readiness_score: 75.43", markdown)
        self.assertIn("no_market_action_guidance: true", markdown)
        self.assertIn("OpenRouter Passive Surface Safety Flags", markdown)
        self.assertIn("no_runtime_authority: true", markdown)
        self.assertIn("manual_review_only: true", markdown)

    def test_result_docs_match_and_report_no_forbidden_changes(self):
        _run_write()
        result = _load_json(RESULT)

        self.assertEqual(result, _load_json(LANE_RESULT))
        self.assertEqual(result["status"], "completed_ready_for_review")
        self.assertEqual(result["codex_lane"], "CODEX_A")
        self.assertEqual(result["branch"], "codex/a-operator-review-pack-round003")
        self.assertEqual(result["base_commit"], "21edc9af372e9d1736afb0eccd3c016f23f2c144")
        self.assertFalse(result["forbidden_changes_detected"])
        self.assertEqual(result["manual_llm_review_queue"]["queue_items_total"], 15)
        self.assertEqual(
            result["manual_llm_review_queue"]["queue_status_counts"]["ready_for_manual_packet_export"],
            0,
        )
        self.assertEqual(
            result["manual_llm_review_queue"]["queue_status_counts"]["waiting_for_operator_pasted_response"],
            14,
        )
        self.assertEqual(
            result["manual_llm_review_queue"]["queue_status_counts"]["response_accepted_for_operator_review"],
            1,
        )
        self.assertTrue(result["manual_llm_review_queue"]["offline_manual_only"])
        self.assertEqual(result["openrouter_passive_surface"]["artifact_status"], "present")
        self.assertEqual(result["openrouter_passive_surface"]["source_048_status"], "completed_pushed")
        self.assertEqual(result["openrouter_passive_surface"]["source_052_status"], "completed_pushed")
        self.assertEqual(
            result["openrouter_passive_surface"]["surfaced_market_ids"],
            ["569344", "569366", "569368", "569373", "573656"],
        )
        self.assertEqual(result["openrouter_passive_surface"]["model"], "anthropic/claude-sonnet-4.5")
        self.assertEqual(result["openrouter_passive_surface"]["total_calls"], 5)
        self.assertEqual(
            result["openrouter_passive_surface"]["quality_summary"]["accepted_for_operator_review_count"],
            5,
        )
        self.assertEqual(
            result["openrouter_passive_surface"]["combined_openrouter_review_contour_summary"]["combined_tokens"],
            48573,
        )
        self.assertEqual(result["openrouter_review_dashboard"]["artifact_status"], "present")
        self.assertEqual(result["openrouter_review_dashboard"]["inventory_summary"]["total_markets_found"], 14)
        self.assertEqual(
            result["openrouter_review_dashboard"]["evidence_readiness_score_summary"]["medium_count"],
            10,
        )
        self.assertEqual(
            result["openrouter_review_dashboard"]["evidence_readiness_score_summary"]["low_count"],
            4,
        )
        self.assertEqual(
            result["openrouter_review_dashboard"]["markets_reviewed_vs_unreviewed"][
                "unreviewed_market_ids"
            ],
            ["597964", "598936", "691547", "692258"],
        )
        self.assertTrue(result["openrouter_review_dashboard"]["no_market_action_guidance"])
        gate = result["packet_completeness_readiness_gate"]
        self.assertEqual(gate["artifact_pointer"], "pm_bot/llm/current_llm_batch_readiness_gate.v1.json")
        self.assertEqual(gate["total_markets"], 14)
        self.assertEqual(gate["medium_count"], 10)
        self.assertEqual(gate["low_count"], 4)
        self.assertEqual(gate["eligible_for_future_llm_review_count"], 10)
        self.assertEqual(gate["eligible_for_future_openrouter_batch_count"], 10)
        self.assertEqual(gate["needs_local_enrichment_count"], 14)
        self.assertEqual(
            gate["low_readiness_market_ids"],
            ["597964", "598936", "691547", "692258"],
        )
        self.assertFalse(gate["future_live_batch_scheduled"])
        self.assertFalse(gate["future_openrouter_batch_approved"])
        self.assertTrue(gate["no_market_action_guidance"])
        self.assertTrue(result["openrouter_passive_surface"]["safety_summary"]["operator_review_only"])
        self.assertTrue(result["openrouter_passive_surface"]["safety_summary"]["passive_context_only"])
        self.assertEqual(
            result["openrouter_passive_surface"]["safety_summary"]["openrouter_calls_performed"],
            0,
        )
        self.assertEqual(
            result["openrouter_passive_surface"]["safety_summary"]["polymarket_api_calls_performed"],
            0,
        )
        self.assertEqual(result["paper_orders_created"], 0)
        self.assertEqual(result["commands_executed"], 0)
        self.assertEqual(result["network_calls"], 0)
        self.assertEqual(result["blockers"], [])

    def test_runner_uses_standard_library_and_no_runtime_surfaces(self):
        _run_write()
        module = _load_module()
        self.assertEqual(module.SCHEMA_VERSION, "operator_review_pack.v1")

        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "pm_bot", "sys"})

        source_no_spaces = RUNNER.read_text(encoding="utf-8").lower().replace(" ", "")
        forbidden_call_terms = [
            _frag("import", "requests"),
            _frag("requests", "."),
            _frag("import", "httpx"),
            _frag("httpx", "."),
            _frag("import", "openai"),
            _frag("openai", "."),
            _frag("import", "anthropic"),
            _frag("anthropic", "."),
            _frag("urllib", ".", "request"),
            _frag("socket", "."),
            _frag("webbrowser", "."),
            _frag("selenium", "."),
            _frag("playwright", "."),
            _frag("submit", "_", "order", "("),
            _frag("execute", "_", "trade", "("),
            _frag("place", "_", "order", "("),
            _frag("scripts", "/", "dispatcher", ".", "py"),
            _frag("scripts", "/", "run", "_", "codex", ".", "py"),
        ]
        for term in forbidden_call_terms:
            self.assertNotIn(term, source_no_spaces)


if __name__ == "__main__":
    unittest.main()
