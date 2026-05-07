import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SOURCE_001_JSON_ARTIFACTS = [
    "docs/PMBOT_SOURCE_001_RESULT.json",
    "pm_bot/llm/source_evidence_enrichment_requirements.v1.json",
    "pm_bot/llm/current_llm_packet_evidence_readiness_scores.v1.json",
    "pm_bot/llm/source_evidence_gap_plan_by_category.v1.json",
    "pm_bot/llm/llm_market_packet_completeness_contract.v1.json",
    "pm_bot/llm/source_evidence_enrichment_design.v1.json",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.json",
    "pm_bot/workbench/operator_review_pack.v1.json",
    "pm_bot/workbench/operator_workbench_export_run.v1.json",
]

SOURCE_001_SOURCE_JSON_ARTIFACTS = [
    "docs/PMBOT_OPENROUTER_053_RESULT.json",
    "pm_bot/llm/current_llm_market_packet_inventory.v1.json",
    "pm_bot/llm/current_llm_source_evidence_completeness_audit.v1.json",
]

SOURCE_001_PUBLIC_MARKDOWN_ARTIFACTS = [
    "docs/PMBOT_SOURCE_001_EVIDENCE_ENRICHMENT_DESIGN_FROM_INVENTORY.md",
    "docs/PMBOT_SOURCE_EVIDENCE_ENRICHMENT_DESIGN.md",
    "pm_bot/llm/source_evidence_enrichment_requirements.v1.md",
    "pm_bot/llm/current_llm_packet_evidence_readiness_scores.v1.md",
    "pm_bot/llm/source_evidence_gap_plan_by_category.v1.md",
    "pm_bot/llm/llm_market_packet_completeness_contract.v1.md",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.md",
    "pm_bot/workbench/operator_review_pack.v1.md",
    "pm_bot/workbench/operator_workbench_export_run.v1.md",
]

SOURCE_002_JSON_ARTIFACTS = [
    "docs/PMBOT_SOURCE_002_RESULT.json",
    "pm_bot/llm/current_llm_batch_readiness_gate.v1.json",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.json",
    "pm_bot/workbench/operator_review_pack.v1.json",
    "pm_bot/workbench/operator_workbench_export_run.v1.json",
]

SOURCE_002_PUBLIC_MARKDOWN_ARTIFACTS = [
    "docs/PMBOT_SOURCE_002_LOCAL_PACKET_COMPLETENESS_SCORER_INTEGRATION.md",
    "pm_bot/llm/current_llm_batch_readiness_gate.v1.md",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.md",
    "pm_bot/workbench/operator_review_pack.v1.md",
    "pm_bot/workbench/operator_workbench_export_run.v1.md",
]

SOURCE_003_JSON_ARTIFACTS = [
    "docs/PMBOT_SOURCE_003_RESULT.json",
    "pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.json",
    "pm_bot/llm/current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.json",
    "pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.json",
    "pm_bot/llm/local_source_enrichment_action_plan.v1.json",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.json",
    "pm_bot/workbench/operator_review_pack.v1.json",
    "pm_bot/workbench/operator_workbench_export_run.v1.json",
]

SOURCE_003_PUBLIC_MARKDOWN_ARTIFACTS = [
    "docs/PMBOT_SOURCE_003_RESOLUTION_SOURCE_FIELD_NORMALIZATION.md",
    "pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.md",
    "pm_bot/llm/current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.md",
    "pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.md",
    "pm_bot/llm/local_source_enrichment_action_plan.v1.md",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.md",
    "pm_bot/workbench/operator_review_pack.v1.md",
    "pm_bot/workbench/operator_workbench_export_run.v1.md",
]

SOURCE_004_JSON_ARTIFACTS = [
    "docs/PMBOT_SOURCE_004_RESULT.json",
    "pm_bot/llm/manual_resolution_source_capture_schema.v1.json",
    "pm_bot/llm/manual_resolution_source_capture_manifest.v1.json",
    "pm_bot/llm/manual_resolution_source_capture_validation.v1.json",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.json",
    "pm_bot/workbench/operator_review_pack.v1.json",
    "pm_bot/workbench/operator_workbench_export_run.v1.json",
]

SOURCE_004_PUBLIC_MARKDOWN_ARTIFACTS = [
    "docs/PMBOT_SOURCE_004_LOCAL_MANUAL_RESOLUTION_SOURCE_CAPTURE_PACKETS.md",
    "pm_bot/llm/manual_resolution_source_capture_schema.v1.md",
    "pm_bot/llm/manual_resolution_source_capture_manifest.v1.md",
    "pm_bot/llm/manual_resolution_source_capture_validation.v1.md",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.md",
    "pm_bot/workbench/operator_review_pack.v1.md",
    "pm_bot/workbench/operator_workbench_export_run.v1.md",
]

SOURCE_003_JSON_ARTIFACTS = [
    "docs/PMBOT_SOURCE_003_RESULT.json",
    "pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.json",
    "pm_bot/llm/current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.json",
    "pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.json",
    "pm_bot/llm/local_source_enrichment_action_plan.v1.json",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.json",
    "pm_bot/workbench/operator_review_pack.v1.json",
    "pm_bot/workbench/operator_workbench_export_run.v1.json",
]

SOURCE_003_PUBLIC_MARKDOWN_ARTIFACTS = [
    "docs/PMBOT_SOURCE_003_RESOLUTION_SOURCE_FIELD_NORMALIZATION.md",
    "pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.md",
    "pm_bot/llm/current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.md",
    "pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.md",
    "pm_bot/llm/local_source_enrichment_action_plan.v1.md",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.md",
    "pm_bot/workbench/operator_review_pack.v1.md",
    "pm_bot/workbench/operator_workbench_export_run.v1.md",
]


def _load_result(name: str) -> dict:
    path = ROOT / "docs" / name
    return json.loads(path.read_text(encoding="utf-8"))


def _frag(*parts: str) -> str:
    return "".join(parts)


def test_openrouter_037_status_is_reconciled_before_retry_artifacts():
    result_037 = _load_result("PMBOT_OPENROUTER_037_RESULT.json")
    result_038 = _load_result("PMBOT_OPENROUTER_038_RESULT.json")
    result_039 = _load_result("PMBOT_OPENROUTER_039_RESULT.json")

    assert result_037["status"] == "completed_pushed"
    assert result_037["commit_hash"] == "5dbc94872527194cb139d1159990062616079e50"
    assert result_037["pushed"] is True
    assert result_037["openrouter_calls_performed"] == 0

    assert result_038["status"] == "blocked_precheck_failed"
    assert result_038["total_openrouter_calls_performed"] == 0
    assert (
        result_038["fail_fast_reason"]
        == "precheck_failed:037_result_status_expected_completed_pushed_actual_completed_local_checks_passed_pending_commit_push"
    )
    assert result_039["source_037_status_before"] == "completed_local_checks_passed_pending_commit_push"
    assert result_039["source_037_status_after"] == "completed_pushed"
    assert result_039["source_037_reconciled"] is True
    assert result_039["source_038_preserved_as_blocked"] is True
    assert result_039["source_038_openrouter_calls_performed"] == 0


def test_openrouter_041_records_fenced_json_normalization_policy():
    result_040 = _load_result("PMBOT_OPENROUTER_040_RESULT.json")
    result_041 = _load_result("PMBOT_OPENROUTER_041_RESULT.json")

    assert result_040["status"] == "blocked_markdown_fence_detected"
    assert result_040["total_openrouter_calls_performed"] == 1
    assert result_040["fail_fast_reason"] == "markdown_fence_detected:569333"

    assert result_041["task_id"] == "PMBOT-OPENROUTER-041-FENCED-JSON-NORMALIZATION-POLICY"
    assert result_041["status"] == "completed_pushed"
    assert result_041["openrouter_calls_performed"] == 0
    assert result_041["polymarket_api_calls_performed"] == 0
    assert result_041["source_040_status"] == "blocked_markdown_fence_detected"
    assert result_041["source_040_fail_fast_reason"] == "markdown_fence_detected:569333"
    assert result_041["fenced_json_normalization_policy_added"] is True
    assert result_041["normalization_policy_version"] == "fenced_json_normalization.v1"
    assert result_041["semantic_repair_allowed"] is False
    assert result_041["raw_response_preserved"] is True
    assert result_041["raw_strict_json_parse_remains_strict"] is True
    assert result_041["secret_scan_passed"] is True
    assert result_041["safety_summary"]["openrouter_calls_performed"] == 0
    assert result_041["safety_summary"]["polymarket_api_calls_performed"] == 0


def test_openrouter_042_records_prohibited_content_block_inputs():
    result_042 = _load_result("PMBOT_OPENROUTER_042_RESULT.json")

    assert result_042["status"] == "blocked_prohibited_content_detected"
    assert result_042["fail_fast_reason"] == "prohibited_content_detected:569334"
    assert result_042["total_openrouter_calls_performed"] == 2
    assert result_042["attempted_market_ids"] == ["569333", "569334"]
    assert result_042["completed_market_ids"] == ["569333"]
    assert result_042["skipped_market_ids"] == ["569343"]
    safety = result_042["safety_boundary_summary"]
    assert safety["no_polymarket_api_calls"] is True
    assert safety["no_wallet_orders_trading"] is True
    assert safety["no_runtime_dispatcher_background_browser_queue_changes"] is True
    assert safety["api_key_value_printed"] is False
    assert safety["api_key_value_written"] is False
    assert safety["api_key_leaked"] is False


def test_openrouter_043_records_local_only_prohibited_content_diagnostic():
    result_043 = _load_result("PMBOT_OPENROUTER_043_RESULT.json")

    assert result_043["task_id"] == "PMBOT-OPENROUTER-043-ANALYZE-042-PROHIBITED-CONTENT-BLOCK"
    assert result_043["status"] == "completed_pushed"
    assert result_043["openrouter_calls_performed"] == 0
    assert result_043["polymarket_api_calls_performed"] == 0
    assert result_043["source_042_status"] == "blocked_prohibited_content_detected"
    assert result_043["source_042_fail_fast_reason"] == "prohibited_content_detected:569334"
    assert result_043["analyzed_market_id"] == "569334"
    assert result_043["diagnostic_classification"] == "false_positive_validator_rule"
    assert result_043["prohibited_content_true_positive"] is False
    assert result_043["prohibited_content_false_positive"] is True
    assert result_043["prohibited_content_uncertain"] is False
    assert result_043["validator_reporting_improved"] is True
    assert result_043["prompt_hardening_performed"] is True
    assert result_043["secret_scan_passed"] is True
    assert result_043["safety_summary"]["openrouter_calls_performed"] == 0
    assert result_043["safety_summary"]["polymarket_api_calls_performed"] == 0


def test_openrouter_045_records_local_only_acceptance_forbidden_phrase_diagnostic():
    result_045 = _load_result("PMBOT_OPENROUTER_045_RESULT.json")

    assert result_045["task_id"] == "PMBOT-OPENROUTER-045-ANALYZE-044-ACCEPTANCE-FORBIDDEN-PHRASE-EDGE"
    assert result_045["status"] == "completed_pushed"
    assert result_045["openrouter_calls_performed"] == 0
    assert result_045["polymarket_api_calls_performed"] == 0
    assert result_045["source_044_status"] == "blocked_acceptance_failed"
    assert (
        result_045["source_044_fail_fast_reason"]
        == "acceptance_gate_failed:569334:response_schema:forbidden_phrase:edge"
    )
    assert result_045["analyzed_market_id"] == "569334"
    assert result_045["diagnostic_classification"] == "false_positive_contextual_phrase"
    assert result_045["acceptance_gate_reporting_improved"] is True
    assert result_045["prompt_hardening_performed"] is True
    assert result_045["schema_or_fixture_changes_performed"] is True
    assert result_045["forbidden_phrase"] == "edge"
    assert result_045["forbidden_phrase_field_path"] == "operator_review_checklist[9]"
    assert result_045["preserve_block_behavior"] is True
    assert result_045["secret_scan_passed"] is True
    assert result_045["safety_summary"]["openrouter_calls_performed"] == 0
    assert result_045["safety_summary"]["polymarket_api_calls_performed"] == 0


def test_openrouter_047_records_local_only_small_batch_quality_baseline():
    result_046 = _load_result("PMBOT_OPENROUTER_046_RESULT.json")
    result_047 = _load_result("PMBOT_OPENROUTER_047_RESULT.json")
    baseline = json.loads(
        (ROOT / "pm_bot" / "llm" / "openrouter_046_small_batch_quality_baseline.v1.json").read_text(
            encoding="utf-8"
        )
    )

    assert result_047["task_id"] == (
        "PMBOT-OPENROUTER-047-SMALL-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY"
    )
    assert result_047["status"] == "completed_pushed"
    assert result_047["openrouter_calls_performed"] == 0
    assert result_047["polymarket_api_calls_performed"] == 0
    assert result_047["source_046_status"] == "completed_pushed"
    assert result_047["source_046_completed_market_ids"] == ["569333", "569334", "569343"]
    assert result_047["source_046_completed_market_ids"] == result_046["completed_market_ids"]
    assert result_047["source_046_total_openrouter_calls_performed"] == 3
    assert result_047["baseline_created"] is True
    assert result_047["operator_summary_created"] is True
    assert result_047["normalization_summary"]["normalization_policy_version"] == (
        "fenced_json_normalization.v1"
    )
    assert result_047["normalization_summary"]["fenced_response_count"] == 3
    assert result_047["normalization_summary"]["normalized_response_count"] == 3
    assert result_047["normalization_summary"]["clean_raw_json_response_count"] == 0
    assert result_047["quality_summary"]["accepted_for_operator_review_count"] == 3
    assert result_047["quality_summary"]["blocked_count"] == 0
    assert result_047["quality_summary"]["baseline_suitable_for_future_controlled_expansion"] is True
    assert result_047["safety_summary"]["openrouter_calls_performed"] == 0
    assert result_047["safety_summary"]["polymarket_api_calls_performed"] == 0
    assert result_047["safety_summary"]["api_key_accessed"] is False

    assert baseline["artifact_type"] == "openrouter_046_small_batch_quality_baseline.v1"
    assert baseline["source_status"] == "completed_pushed"
    assert baseline["aggregate"]["source_openrouter_calls_performed"] == 3
    assert baseline["aggregate"]["fenced_response_count"] == 3
    assert baseline["aggregate"]["normalized_response_count"] == 3
    assert baseline["aggregate"]["clean_raw_json_response_count"] == 0
    assert baseline["quality_summary"]["all_completed_markets_have_operator_checklists"] is True
    assert baseline["future_readiness_note"]["option_a"]["run_or_approved_by_047"] is False
    assert baseline["future_readiness_note"]["option_b"]["run_or_approved_by_047"] is False


def test_openrouter_049_records_workbench_passive_surface_integration():
    result_048 = _load_result("PMBOT_OPENROUTER_048_RESULT.json")
    result_049 = _load_result("PMBOT_OPENROUTER_049_RESULT.json")
    pointer = json.loads(
        (ROOT / "pm_bot" / "workbench" / "openrouter_passive_surface_pointer.v1.json").read_text(
            encoding="utf-8"
        )
    )
    n3_pointer = pointer["surface_history"][0]

    assert result_049["task_id"] == "PMBOT-OPENROUTER-049-WORKBENCH-PASSIVE-SURFACE-INTEGRATION"
    assert result_049["status"] == "completed_pushed"
    assert result_049["head_before"] == "6ecd297901366e9679257ac535cbe3f99de995de"
    assert result_049["openrouter_calls_performed"] == 0
    assert result_049["polymarket_api_calls_performed"] == 0
    assert result_049["source_048_status"] == "completed_pushed"
    assert result_049["source_048_status"] == result_048["status"]
    assert result_049["workbench_passive_surface_integrated"] is True
    assert result_049["surfaced_market_ids"] == ["569333", "569334", "569343"]
    assert result_049["surfaced_market_ids"] == n3_pointer["surfaced_market_ids"]
    assert result_049["aggregate_usage"] == n3_pointer["aggregate_usage"]
    assert result_049["aggregate_cost"] == n3_pointer["aggregate_cost"]
    assert result_049["normalization_summary"] == n3_pointer["normalization_summary"]
    assert result_049["quality_summary"] == n3_pointer["quality_summary"]
    assert pointer["latest_surface_source_batch_task"] == (
        "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL"
    )
    assert pointer["combined_openrouter_review_contour_summary"]["combined_tokens"] == 48573

    safety = result_049["safety_summary"]
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
        assert safety[flag] is True

    assert safety["openrouter_calls_performed"] == 0
    assert safety["polymarket_api_calls_performed"] == 0
    assert safety["network_calls"] == 0
    assert safety["orders_created"] == 0
    assert safety["runtime_wiring_added"] is False
    assert safety["dispatcher_changes_added"] is False
    assert safety["background_workers_added"] is False
    assert safety["queue_items_created"] is False
    assert safety["queue_state_mutated"] is False
    assert safety["browser_automation_added"] is False
    assert safety["wallet_or_order_access_added"] is False
    assert safety["raw_model_responses_included"] is False
    assert safety["per_market_response_text_included"] is False
    assert result_049["secret_scan_passed"] is True
    assert result_049["pushed"] is True
    assert result_049["working_tree_clean_after"] is True


def test_openrouter_052_records_local_only_n5_batch_quality_baseline():
    result_051 = _load_result("PMBOT_OPENROUTER_051_RESULT.json")
    result_052 = _load_result("PMBOT_OPENROUTER_052_RESULT.json")
    baseline = json.loads(
        (ROOT / "pm_bot" / "llm" / "openrouter_051_n5_batch_quality_baseline.v1.json").read_text(
            encoding="utf-8"
        )
    )

    expected_market_ids = ["569344", "569366", "569368", "569373", "573656"]

    assert result_052["task_id"] == (
        "PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY"
    )
    assert result_052["status"] == "completed_pushed"
    assert result_052["head_before"] == "64d1c67726ffc6891b48641088322ed1e6ecf8c4"
    assert result_052["openrouter_calls_performed"] == 0
    assert result_052["polymarket_api_calls_performed"] == 0
    assert result_052["source_051_status"] == "completed_pushed"
    assert result_052["source_051_completed_market_ids"] == expected_market_ids
    assert result_052["source_051_completed_market_ids"] == result_051["completed_market_ids"]
    assert result_052["source_051_total_openrouter_calls_performed"] == 5
    assert result_052["baseline_created"] is True
    assert result_052["operator_summary_created"] is True
    assert result_052["analyzed_market_ids"] == expected_market_ids
    assert result_052["aggregate_usage"]["total_tokens"] == 29887
    assert result_052["aggregate_cost"]["total_cost"] == 0.199089
    assert result_052["estimated_vs_actual_tokens"]["estimated_total_tokens"] == 31143.333335
    assert result_052["estimated_vs_actual_tokens"]["actual_under_estimate"] is True
    assert result_052["estimated_vs_actual_cost"]["estimated_total_cost"] == 0.20997
    assert result_052["estimated_vs_actual_cost"]["actual_under_estimate"] is True
    assert result_052["estimated_vs_actual_cost"]["cost_cap_exceeded"] is False
    assert result_052["normalization_summary"]["normalization_policy_version"] == (
        "fenced_json_normalization.v1"
    )
    assert result_052["normalization_summary"]["fenced_response_count"] == 5
    assert result_052["normalization_summary"]["normalized_response_count"] == 5
    assert result_052["normalization_summary"]["clean_raw_json_response_count"] == 0
    assert result_052["quality_summary"]["accepted_for_operator_review_count"] == 5
    assert result_052["quality_summary"]["blocked_count"] == 0
    assert result_052["quality_summary"]["baseline_suitable_for_future_controlled_expansion"] is True
    assert result_052["secret_scan_passed"] is True

    safety = result_052["safety_summary"]
    assert safety["openrouter_calls_performed"] == 0
    assert safety["polymarket_api_calls_performed"] == 0
    assert safety["api_key_accessed"] is False
    assert safety["no_wallet_orders_trading"] is True
    assert safety["no_runtime_dispatcher_background_browser_queue_changes"] is True
    assert safety["no_browser_automation"] is True
    assert safety["no_queue_mutation"] is True
    assert safety["acceptance_is_not_trading_approval"] is True
    assert safety["no_recommendations"] is True
    assert safety["no_market_decision"] is True

    assert baseline["artifact_type"] == "openrouter_051_n5_batch_quality_baseline.v1"
    assert baseline["source_status"] == "completed_pushed"
    assert baseline["aggregate"]["source_openrouter_calls_performed"] == 5
    assert baseline["aggregate"]["attempted_market_count"] == 5
    assert baseline["aggregate"]["completed_market_count"] == 5
    assert baseline["aggregate"]["skipped_market_count"] == 0
    assert baseline["aggregate"]["fenced_response_count"] == 5
    assert baseline["aggregate"]["normalized_response_count"] == 5
    assert baseline["aggregate"]["clean_raw_json_response_count"] == 0
    assert baseline["aggregate"]["accepted_for_operator_review_count"] == 5
    assert baseline["aggregate"]["blocked_count"] == 0
    assert baseline["aggregate"]["estimated_vs_actual_cost"]["actual_total_cost"] == 0.199089
    assert baseline["quality_summary"]["all_completed_markets_have_operator_checklists"] is True
    assert baseline["quality_summary"]["baseline_judgment"] == (
        "suitable_local_baseline_for_future_protocol_work"
    )
    assert len(baseline["per_market"]) == 5
    assert [item["market_id"] for item in baseline["per_market"]] == expected_market_ids
    assert all(item["accepted_for_operator_review"] is True for item in baseline["per_market"])
    assert all(item["quality_warnings"] for item in baseline["per_market"])
    assert baseline["future_readiness_note"]["option_a"]["run_or_approved_by_052"] is False
    assert baseline["future_readiness_note"]["option_b"]["run_or_approved_by_052"] is False


def test_openrouter_053_records_n5_surface_workbench_inventory_ux_and_contour_audit():
    result_053 = _load_result("PMBOT_OPENROUTER_053_RESULT.json")

    assert result_053["task_id"] == (
        "PMBOT-OPENROUTER-053-N5-SURFACE-WORKBENCH-INVENTORY-UX-AND-CONTOUR-AUDIT"
    )
    assert result_053["status"] in {
        "completed_local_validation_pending_commit_push",
        "completed_pushed",
    }
    assert result_053["head_before"] == "bb46543c7ffb0efa66c76229f8c58951850376b1"
    assert result_053["openrouter_calls_performed"] == 0
    assert result_053["polymarket_api_calls_performed"] == 0
    assert result_053["source_051_status"] == "completed_pushed"
    assert result_053["source_052_status"] == "completed_pushed"
    assert result_053["n5_passive_operator_surface_created"] is True
    assert result_053["n5_workbench_integration_completed"] is True
    assert result_053["contour_audit_created"] is True
    assert result_053["market_packet_inventory_created"] is True
    assert result_053["source_evidence_audit_created"] is True
    assert result_053["operator_dashboard_created"] is True
    assert result_053["operator_runbook_created"] is True
    assert result_053["next_step_decision_matrix_created"] is True
    assert result_053["surfaced_market_ids"] == ["569344", "569366", "569368", "569373", "573656"]
    for market_id in [
        "563650",
        "569332",
        "569333",
        "569334",
        "569343",
        "569344",
        "569366",
        "569368",
        "569373",
        "573656",
    ]:
        assert market_id in result_053["inventory_market_ids"]

    combined = result_053["combined_openrouter_contour_summary"]
    assert combined["total_markets_successfully_reviewed"] == 8
    assert combined["total_openrouter_calls_in_successful_batches"] == 8
    assert combined["combined_cost"] == 0.325071
    assert combined["combined_tokens"] == 48573
    assert combined["total_blocked_in_successful_batches"] == 0

    assert result_053["normalization_summary"]["successful_batch_responses_requiring_fenced_normalization"] == "8/8"
    assert result_053["normalization_summary"]["clean_raw_json_response_count"] == 0
    assert result_053["quality_summary"]["accepted_for_operator_review_count"] == 8
    assert result_053["quality_summary"]["blocked_count"] == 0
    assert result_053["inventory_summary"]["total_markets_found"] == 14
    assert result_053["inventory_summary"]["total_reviewed_by_openrouter"] == 10
    assert result_053["evidence_completeness_summary"]["reviewed_market_count"] == 10
    assert result_053["safety_summary"]["openrouter_calls_performed_by_this_task"] == 0
    assert result_053["safety_summary"]["polymarket_api_calls_performed_by_this_task"] == 0
    assert result_053["safety_summary"]["api_key_accessed"] is False


def test_source_001_result_records_local_evidence_enrichment_design():
    result = _load_result("PMBOT_SOURCE_001_RESULT.json")

    assert result["task_id"] == "PMBOT-SOURCE-001-EVIDENCE-ENRICHMENT-DESIGN-FROM-INVENTORY"
    assert result["status"] in {
        "completed_local_validation_pending_commit_push",
        "completed_pushed",
    }
    assert result["head_before"] == "aa2b8a982cd383d2211f818d33ccbf7ae3c27362"
    assert result["openrouter_calls_performed"] == 0
    assert result["polymarket_api_calls_performed"] == 0
    assert result["external_network_calls_performed"] == 0
    assert result["source_053_status"] == "completed_pushed"
    assert result["enrichment_requirements_created"] is True
    assert result["readiness_scores_created"] is True
    assert result["category_gap_plan_created"] is True
    assert result["completeness_contract_created"] is True
    assert result["enrichment_design_created"] is True
    assert result["workbench_dashboard_updated"] is True
    assert result["inventory_market_count"] == 14
    assert result["scored_market_count"] == 14
    assert result["category_count"] == 5
    assert result["evidence_readiness_summary"]["medium_count"] == 10
    assert result["evidence_readiness_summary"]["low_count"] == 4
    assert result["secret_scan_passed"] is True
    assert result["safety_summary"]["no_market_action_guidance"] is True
    assert result["safety_summary"]["api_key_accessed"] is False
    assert result["safety_summary"]["queue_state_mutated"] is False
    assert result["safety_summary"]["runtime_wiring_added"] is False
    assert result["safety_summary"]["browser_automation_used"] is False


def test_source_001_json_artifacts_parse_and_source_artifacts_remain_valid():
    for path in SOURCE_001_JSON_ARTIFACTS + SOURCE_001_SOURCE_JSON_ARTIFACTS:
        payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
        assert isinstance(payload, dict), path

    dashboard = json.loads(
        (ROOT / "pm_bot" / "workbench" / "operator_openrouter_review_dashboard.v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert dashboard["n3_summary"]["calls"] == 3
    assert dashboard["n5_summary"]["calls"] == 5
    assert dashboard["combined_openrouter_review_contour_summary"]["combined_tokens"] == 48573
    assert dashboard["evidence_readiness_score_summary"]["medium_count"] == 10
    assert dashboard["evidence_readiness_score_summary"]["low_count"] == 4
    assert dashboard["safety_summary"]["operator_review_only"] is True
    assert dashboard["safety_summary"]["no_queue_authority"] is True
    assert dashboard["safety_summary"]["no_runtime_authority"] is True
    assert dashboard["safety_summary"]["no_dispatcher_authority"] is True
    assert dashboard["safety_summary"]["no_wallet_or_order_authority"] is True
    assert dashboard["safety_summary"]["acceptance_is_not_trading_approval"] is True


def test_source_001_public_markdown_and_changed_files_pass_safety_scans():
    forbidden_markdown_phrases = [
        "buy recommendation",
        "sell recommendation",
        "hold recommendation",
        "enter position",
        "exit position",
        "recommended side",
        "place an order",
        "submit an order",
        "market action recommendation",
    ]
    for path in SOURCE_001_PUBLIC_MARKDOWN_ARTIFACTS:
        text = (ROOT / path).read_text(encoding="utf-8").lower()
        for phrase in forbidden_markdown_phrases:
            assert phrase not in text, path

    secret_name = _frag("OPENROUTER", "_API", "_KEY")
    result = _load_result("PMBOT_SOURCE_001_RESULT.json")
    for path in result["files_changed"]:
        text = (ROOT / path).read_text(encoding="utf-8", errors="ignore")
        assert secret_name not in text, path


def test_source_002_result_records_local_packet_completeness_gate():
    result = _load_result("PMBOT_SOURCE_002_RESULT.json")

    assert result["task_id"] == "PMBOT-SOURCE-002-LOCAL-PACKET-COMPLETENESS-SCORER-INTEGRATION"
    assert result["status"] in {
        "completed_local_validation_pending_commit_push",
        "completed_pushed",
    }
    assert result["head_before"] == "ee4562eaa920d592019d8db6387a9cd66dc3b5e6"
    assert result["openrouter_calls_performed"] == 0
    assert result["polymarket_api_calls_performed"] == 0
    assert result["external_network_calls_performed"] == 0
    assert result["source_001_status"] == "completed_pushed"
    assert result["scorer_module_created"] is True
    assert result["batch_readiness_gate_created"] is True
    assert result["workbench_dashboard_updated"] is True
    assert result["inventory_market_count"] == 14
    assert result["scored_market_count"] == 14
    assert result["high_count"] == 0
    assert result["medium_count"] == 10
    assert result["low_count"] == 4
    assert result["blocked_count"] == 0
    assert result["eligible_for_future_llm_review_count"] == 10
    assert result["eligible_for_future_openrouter_batch_count"] == 10
    assert result["needs_local_enrichment_count"] == 14
    assert result["secret_scan_passed"] is True
    assert result["safety_summary"]["operator_review_only"] is True
    assert result["safety_summary"]["no_market_action_guidance"] is True
    assert result["safety_summary"]["api_key_accessed"] is False
    assert result["safety_summary"]["queue_state_mutated"] is False
    assert result["safety_summary"]["runtime_wiring_added"] is False
    assert result["safety_summary"]["browser_automation_used"] is False


def test_source_002_json_artifacts_parse_and_gate_is_reflected_in_workbench():
    for path in SOURCE_002_JSON_ARTIFACTS:
        payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
        assert isinstance(payload, dict), path

    gate = json.loads(
        (ROOT / "pm_bot" / "llm" / "current_llm_batch_readiness_gate.v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert gate["total_markets"] == 14
    assert gate["low_readiness_market_ids"] == ["597964", "598936", "691547", "692258"]
    assert gate["future_live_batch_scheduled"] is False
    assert gate["future_openrouter_batch_approved"] is False
    assert gate["safety_flags"]["no_queue_authority"] is True
    assert gate["safety_flags"]["no_runtime_authority"] is True
    assert gate["safety_flags"]["no_market_action_guidance"] is True

    dashboard = json.loads(
        (ROOT / "pm_bot" / "workbench" / "operator_openrouter_review_dashboard.v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert dashboard["batch_readiness_gate_summary"]["total_markets"] == 14
    assert dashboard["batch_readiness_gate_summary"]["low_count"] == 4
    assert (
        dashboard["batch_readiness_gate_summary"]["artifact_pointer"]
        == "pm_bot/llm/current_llm_batch_readiness_gate.v1.json"
    )

    review_pack = json.loads(
        (ROOT / "pm_bot" / "workbench" / "operator_review_pack.v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert (
        review_pack["packet_completeness_readiness_gate"]["artifact_pointer"]
        == "pm_bot/llm/current_llm_batch_readiness_gate.v1.json"
    )


def test_source_002_public_markdown_and_changed_files_pass_safety_scans():
    forbidden_markdown_phrases = [
        "buy recommendation",
        "sell recommendation",
        "hold recommendation",
        "enter position",
        "exit position",
        "recommended side",
        "place an order",
        "submit an order",
        "market action recommendation",
    ]
    for path in SOURCE_002_PUBLIC_MARKDOWN_ARTIFACTS:
        text = (ROOT / path).read_text(encoding="utf-8").lower()
        for phrase in forbidden_markdown_phrases:
            assert phrase not in text, path

    secret_name = _frag("OPENROUTER", "_API", "_KEY")
    result = _load_result("PMBOT_SOURCE_002_RESULT.json")
    for path in result["files_changed"]:
        text = (ROOT / path).read_text(encoding="utf-8", errors="ignore")
        assert secret_name not in text, path


def test_source_003_result_records_local_resolution_source_normalization():
    result = _load_result("PMBOT_SOURCE_003_RESULT.json")

    assert result["task_id"] == "PMBOT-SOURCE-003-RESOLUTION-SOURCE-FIELD-NORMALIZATION"
    assert result["status"] == "completed_pushed"
    assert result["head_before"] == "303048bf4a734ebd44f32990055cc30931e180a2"
    assert result["pushed"] is True
    assert result["openrouter_calls_performed"] == 0
    assert result["polymarket_api_calls_performed"] == 0
    assert result["external_network_calls_performed"] == 0
    assert result["source_001_status"] == "completed_pushed"
    assert result["source_002_status"] == "completed_pushed"
    assert result["normalizer_module_created"] is True
    assert result["resolution_source_audit_created"] is True
    assert result["after_normalization_readiness_scores_created"] is True
    assert result["after_normalization_batch_readiness_gate_created"] is True
    assert result["workbench_dashboard_updated"] is True
    assert result["local_enrichment_action_plan_created"] is True
    assert result["markets_audited_count"] == 14
    assert result["markets_with_resolution_criteria_text"] == 0
    assert result["markets_missing_resolution_criteria_text"] == 14
    assert result["markets_with_full_resolution_rules"] == 0
    assert result["markets_missing_full_resolution_rules"] == 14
    assert result["markets_with_official_source_references"] == 0
    assert result["markets_missing_official_source_references"] == 14
    assert result["previous_readiness_summary"]["medium_count"] == 10
    assert result["updated_readiness_summary"]["medium_count"] == 10
    assert result["updated_readiness_summary"]["low_count"] == 4
    assert result["secret_scan_passed"] is True

    safety = result["safety_summary"]
    assert safety["operator_review_only"] is True
    assert safety["passive_context_only"] is True
    assert safety["no_trading_authority"] is True
    assert safety["no_queue_authority"] is True
    assert safety["no_runtime_authority"] is True
    assert safety["no_dispatcher_authority"] is True
    assert safety["no_wallet_or_order_authority"] is True
    assert safety["no_market_action_guidance"] is True
    assert safety["openrouter_calls_performed_by_this_task"] == 0
    assert safety["polymarket_api_calls_performed_by_this_task"] == 0
    assert safety["external_network_calls_performed_by_this_task"] == 0
    assert safety["api_key_accessed"] is False
    assert safety["queue_state_mutated"] is False
    assert safety["runtime_wiring_added"] is False
    assert safety["browser_automation_used"] is False


def test_source_003_json_artifacts_parse_and_cover_inventory_markets():
    for path in SOURCE_003_JSON_ARTIFACTS:
        payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
        assert isinstance(payload, dict), path

    expected_market_ids = [
        "563650",
        "569332",
        "569333",
        "569334",
        "569343",
        "569344",
        "569366",
        "569368",
        "569373",
        "573656",
        "597964",
        "598936",
        "691547",
        "692258",
    ]
    audit = json.loads(
        (
            ROOT
            / "pm_bot"
            / "llm"
            / "current_llm_resolution_source_normalization_audit.v1.json"
        ).read_text(encoding="utf-8")
    )
    assert [item["market_id"] for item in audit["markets"]] == expected_market_ids
    assert audit["aggregate"]["total_markets_audited"] == 14
    assert audit["aggregate"]["markets_missing_resolution_criteria_text"] == 14
    assert audit["aggregate"]["markets_missing_full_resolution_rules"] == 14
    assert audit["aggregate"]["markets_missing_official_source_references"] == 14

    required_missing_keys = {
        "full_market_resolution_criteria_text",
        "full_resolution_rules",
        "official_source_references",
        "official_source_urls_or_rule_references",
        "source_timestamps",
        "source_reliability_review",
    }
    for item in audit["markets"]:
        assert required_missing_keys.issubset(set(item["missing_resolution_source_fields"]))
        assert item["full_market_resolution_criteria_text"] is None
        assert item["full_resolution_rules"] is None
        assert item["official_source_references"] == []
        assert item["official_source_urls_or_rule_references"] == []
        assert item["no_market_action_guidance"] is True


def test_source_003_after_readiness_gate_and_action_plan_are_passive_only():
    readiness = json.loads(
        (
            ROOT
            / "pm_bot"
            / "llm"
            / "current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.json"
        ).read_text(encoding="utf-8")
    )
    gate = json.loads(
        (
            ROOT
            / "pm_bot"
            / "llm"
            / "current_llm_batch_readiness_gate_after_source_normalization.v1.json"
        ).read_text(encoding="utf-8")
    )
    action_plan = json.loads(
        (ROOT / "pm_bot" / "llm" / "local_source_enrichment_action_plan.v1.json").read_text(
            encoding="utf-8"
        )
    )

    assert len(readiness["markets"]) == 14
    assert readiness["aggregate"]["previous_medium_count"] == 10
    assert readiness["aggregate"]["updated_medium_count"] == 10
    assert readiness["aggregate"]["updated_low_count"] == 4
    assert readiness["aggregate"]["score_delta_average"] == 0.0
    assert readiness["aggregate"]["markets_improved"] == []
    for item in readiness["markets"]:
        assert 0 <= item["updated_score"] <= 100
        assert item["updated_readiness_band"] in {"high", "medium", "low", "blocked"}
        assert item["delta"] == item["updated_score"] - item["previous_score"]
        assert item["no_market_action_guidance"] is True

    assert gate["total_markets"] == 14
    assert gate["future_live_batch_scheduled"] is False
    assert gate["future_openrouter_batch_approved"] is False
    assert gate["future_llm_review_approved"] is False
    assert gate["safety_flags"]["no_trading_authority"] is True
    assert gate["safety_flags"]["no_queue_authority"] is True
    assert gate["safety_flags"]["no_runtime_authority"] is True
    assert gate["safety_flags"]["no_wallet_or_order_authority"] is True
    assert gate["safety_flags"]["operator_review_only"] is True
    assert gate["safety_flags"]["no_market_action_guidance"] is True

    assert action_plan["aggregate"]["total_actions"] == 14
    assert action_plan["aggregate"]["high_priority_local_actions"] == 4
    assert action_plan["aggregate"]["queue_items_created"] == 0
    assert action_plan["aggregate"]["queue_state_mutated"] is False
    assert action_plan["aggregate"]["runtime_objects_created"] is False
    assert action_plan["aggregate"]["passive_only"] is True
    for item in action_plan["actions"]:
        assert item["requires_external_network"] is False
        assert item["operator_manual_input_needed"] is True
        assert item["no_market_action_guidance"] is True


def test_source_003_workbench_artifacts_surface_resolution_source_status():
    dashboard = json.loads(
        (ROOT / "pm_bot" / "workbench" / "operator_openrouter_review_dashboard.v1.json").read_text(
            encoding="utf-8"
        )
    )
    review_pack = json.loads(
        (ROOT / "pm_bot" / "workbench" / "operator_review_pack.v1.json").read_text(
            encoding="utf-8"
        )
    )
    run = json.loads(
        (
            ROOT
            / "pm_bot"
            / "workbench"
            / "operator_workbench_export_run.v1.json"
        ).read_text(encoding="utf-8")
    )

    assert dashboard["resolution_source_normalization_summary"]["total_markets_audited"] == 14
    assert dashboard["resolution_source_normalization_summary"][
        "markets_missing_resolution_criteria_text"
    ] == 14
    assert (
        dashboard["artifact_pointers"]["resolution_source_audit_json"]
        == "pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.json"
    )
    assert review_pack["resolution_source_normalization"]["total_markets_audited"] == 14
    assert (
        review_pack["resolution_source_normalization"]["audit_artifact_pointer"]
        == "pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.json"
    )
    assert review_pack["resolution_source_normalization"]["passive_only"] is True
    assert run["resolution_source_normalization"]["total_markets_audited"] == 14
    assert run["batch_readiness_gate_after_source_normalization"][
        "future_openrouter_batch_approved"
    ] is False
    assert run["local_source_enrichment_action_plan"]["queue_state_mutated"] is False


def test_source_003_public_markdown_and_changed_files_pass_safety_scans():
    forbidden_markdown_phrases = [
        "buy recommendation",
        "sell recommendation",
        "hold recommendation",
        "enter position",
        "exit position",
        "recommended side",
        "place an order",
        "submit an order",
        "market action recommendation",
    ]
    for path in SOURCE_003_PUBLIC_MARKDOWN_ARTIFACTS:
        text = (ROOT / path).read_text(encoding="utf-8").lower()
        for phrase in forbidden_markdown_phrases:
            assert phrase not in text, path

    secret_name = _frag("OPENROUTER", "_API", "_KEY")
    result = _load_result("PMBOT_SOURCE_003_RESULT.json")
    for path in result["files_changed"]:
        text = (ROOT / path).read_text(encoding="utf-8", errors="ignore")
        assert secret_name not in text, path


def test_source_004_result_records_manual_resolution_source_capture_packets():
    result = _load_result("PMBOT_SOURCE_004_RESULT.json")

    assert result["task_id"] == "PMBOT-SOURCE-004-LOCAL-MANUAL-RESOLUTION-SOURCE-CAPTURE-PACKETS"
    assert result["status"] in {
        "completed_local_validation_pending_push",
        "completed_pushed",
    }
    assert result["head_before"] == "c9d183a29d0655e05db87505e8c3719183e05576"
    assert result["openrouter_calls_performed"] == 0
    assert result["polymarket_api_calls_performed"] == 0
    assert result["external_network_calls_performed"] == 0
    assert result["source_003_status"] == "completed_pushed"
    assert result["capture_schema_created"] is True
    assert result["capture_templates_created"] is True
    assert result["capture_manifest_created"] is True
    assert result["capture_validator_created"] is True
    assert result["capture_validation_report_created"] is True
    assert result["workbench_dashboard_updated"] is True
    assert result["capture_market_count"] == 14
    assert result["capture_json_template_count"] == 14
    assert result["capture_markdown_template_count"] == 14
    assert result["capture_status_counts"]["not_started"] == 14
    assert result["validation_valid_count"] == 14
    assert result["validation_invalid_count"] == 0
    assert result["secret_scan_passed"] is True

    safety = result["safety_summary"]
    assert safety["operator_review_only"] is True
    assert safety["no_market_action_guidance"] is True
    assert safety["no_trading_authority"] is True
    assert safety["no_queue_authority"] is True
    assert safety["no_runtime_authority"] is True
    assert safety["no_wallet_or_order_authority"] is True
    assert safety["api_key_accessed"] is False


def test_source_004_json_artifacts_parse_and_cover_inventory_markets():
    for path in SOURCE_004_JSON_ARTIFACTS:
        payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
        assert isinstance(payload, dict), path

    inventory = json.loads(
        (ROOT / "pm_bot" / "llm" / "current_llm_market_packet_inventory.v1.json").read_text(
            encoding="utf-8"
        )
    )
    expected_market_ids = [item["market_id"] for item in inventory["markets"]]
    capture_dir = ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture"
    json_paths = sorted(capture_dir.glob("*_resolution_source_capture.v1.json"))
    md_paths = sorted(capture_dir.glob("*_resolution_source_capture.v1.md"))

    assert len(json_paths) == 14
    assert len(md_paths) == 14
    assert [path.name.split("_")[0] for path in json_paths] == expected_market_ids
    assert [path.name.split("_")[0] for path in md_paths] == expected_market_ids
    for path in json_paths:
        packet = json.loads(path.read_text(encoding="utf-8"))
        assert packet["source_capture_status"] == "not_started"
        assert packet["no_market_action_guidance"] is True
        assert packet["no_trading_authority"] is True
        assert packet["no_queue_authority"] is True
        assert packet["no_runtime_authority"] is True
        assert packet["no_wallet_or_order_authority"] is True


def test_source_004_manifest_validation_and_workbench_capture_status():
    manifest = json.loads(
        (
            ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_manifest.v1.json"
        ).read_text(encoding="utf-8")
    )
    validation = json.loads(
        (
            ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_validation.v1.json"
        ).read_text(encoding="utf-8")
    )
    dashboard = json.loads(
        (ROOT / "pm_bot" / "workbench" / "operator_openrouter_review_dashboard.v1.json").read_text(
            encoding="utf-8"
        )
    )
    review_pack = json.loads(
        (ROOT / "pm_bot" / "workbench" / "operator_review_pack.v1.json").read_text(
            encoding="utf-8"
        )
    )
    run = json.loads(
        (
            ROOT
            / "pm_bot"
            / "workbench"
            / "operator_workbench_export_run.v1.json"
        ).read_text(encoding="utf-8")
    )

    assert manifest["total_capture_packets"] == 14
    assert manifest["capture_status_counts"]["not_started"] == 14
    assert validation["total_packets_validated"] == 14
    assert validation["valid_count"] == 14
    assert validation["invalid_count"] == 0
    assert dashboard["manual_resolution_source_capture_summary"]["packets_created"] == 14
    assert (
        dashboard["artifact_pointers"]["manual_resolution_source_capture_manifest_json"]
        == "pm_bot/llm/manual_resolution_source_capture_manifest.v1.json"
    )
    assert review_pack["manual_resolution_source_capture"]["packets_not_started"] == 14
    assert run["manual_resolution_source_capture"]["validation_invalid_count"] == 0


def test_source_004_public_markdown_and_changed_files_pass_safety_scans():
    forbidden_markdown_phrases = [
        "buy recommendation",
        "sell recommendation",
        "hold recommendation",
        "enter position",
        "exit position",
        "recommended side",
        "place an order",
        "submit an order",
        "market action recommendation",
    ]
    for path in SOURCE_004_PUBLIC_MARKDOWN_ARTIFACTS:
        text = (ROOT / path).read_text(encoding="utf-8").lower()
        for phrase in forbidden_markdown_phrases:
            assert phrase not in text, path

    secret_name = _frag("OPENROUTER", "_API", "_KEY")
    result = _load_result("PMBOT_SOURCE_004_RESULT.json")
    for path in result["files_changed"]:
        text = (ROOT / path).read_text(encoding="utf-8", errors="ignore")
        assert secret_name not in text, path


def test_source_003_result_records_resolution_source_normalization():
    result = _load_result("PMBOT_SOURCE_003_RESULT.json")

    assert result["task_id"] == "PMBOT-SOURCE-003-RESOLUTION-SOURCE-FIELD-NORMALIZATION"
    assert result["status"] == "completed_pushed"
    assert result["head_before"] == "303048bf4a734ebd44f32990055cc30931e180a2"
    assert result["pushed"] is True
    assert result["openrouter_calls_performed"] == 0
    assert result["polymarket_api_calls_performed"] == 0
    assert result["external_network_calls_performed"] == 0
    assert result["source_001_status"] == "completed_pushed"
    assert result["source_002_status"] == "completed_pushed"
    assert result["normalizer_module_created"] is True
    assert result["resolution_source_audit_created"] is True
    assert result["after_normalization_readiness_scores_created"] is True
    assert result["after_normalization_batch_readiness_gate_created"] is True
    assert result["workbench_dashboard_updated"] is True
    assert result["local_enrichment_action_plan_created"] is True
    assert result["markets_audited_count"] == 14
    assert result["markets_missing_resolution_criteria_text"] == 14
    assert result["markets_missing_full_resolution_rules"] == 14
    assert result["markets_missing_official_source_references"] == 14
    assert result["previous_readiness_summary"]["medium_count"] == 10
    assert result["updated_readiness_summary"]["medium_count"] == 10
    assert result["previous_readiness_summary"]["low_count"] == 4
    assert result["updated_readiness_summary"]["low_count"] == 4
    assert result["secret_scan_passed"] is True
    assert result["safety_summary"]["operator_review_only"] is True
    assert result["safety_summary"]["no_queue_authority"] is True
    assert result["safety_summary"]["no_runtime_authority"] is True
    assert result["safety_summary"]["no_trading_authority"] is True
    assert result["safety_summary"]["no_market_action_guidance"] is True


def test_source_003_json_artifacts_parse_and_workbench_pointers_are_present():
    for path in SOURCE_003_JSON_ARTIFACTS:
        payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
        assert isinstance(payload, dict), path

    audit = json.loads(
        (
            ROOT
            / "pm_bot"
            / "llm"
            / "current_llm_resolution_source_normalization_audit.v1.json"
        ).read_text(encoding="utf-8")
    )
    assert audit["total_markets_audited"] == 14
    assert len(audit["per_market_audit"]) == 14
    for record in audit["per_market_audit"]:
        assert "missing_resolution_source_fields" in record
        assert record["official_source_urls_or_rule_references"] == []
        assert record["full_resolution_rules"] is None

    gate = json.loads(
        (
            ROOT
            / "pm_bot"
            / "llm"
            / "current_llm_batch_readiness_gate_after_source_normalization.v1.json"
        ).read_text(encoding="utf-8")
    )
    assert gate["total_markets"] == 14
    assert gate["future_live_batch_scheduled"] is False
    assert gate["future_openrouter_batch_approved"] is False
    assert gate["safety_flags"]["no_queue_authority"] is True
    assert gate["safety_flags"]["no_runtime_authority"] is True
    assert gate["safety_flags"]["no_market_action_guidance"] is True

    plan = json.loads(
        (ROOT / "pm_bot" / "llm" / "local_source_enrichment_action_plan.v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert plan["queue_mutation_performed"] is False
    assert plan["runtime_objects_created"] is False
    assert plan["dispatcher_integration_added"] is False
    assert all(item["requires_external_network"] is False for item in plan["actions"])

    dashboard = json.loads(
        (ROOT / "pm_bot" / "workbench" / "operator_openrouter_review_dashboard.v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert dashboard["resolution_source_normalization_summary"]["total_markets_audited"] == 14
    assert (
        dashboard["artifact_pointers"]["resolution_source_audit_json"]
        == "pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.json"
    )

    review_pack = json.loads(
        (ROOT / "pm_bot" / "workbench" / "operator_review_pack.v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert (
        review_pack["resolution_source_normalization"]["audit_artifact_pointer"]
        == "pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.json"
    )


def test_source_003_public_markdown_and_changed_files_pass_safety_scans():
    forbidden_markdown_phrases = [
        "buy recommendation",
        "sell recommendation",
        "hold recommendation",
        "enter position",
        "exit position",
        "recommended side",
        "place an order",
        "submit an order",
        "market action recommendation",
    ]
    for path in SOURCE_003_PUBLIC_MARKDOWN_ARTIFACTS:
        text = (ROOT / path).read_text(encoding="utf-8").lower()
        for phrase in forbidden_markdown_phrases:
            assert phrase not in text, path

    secret_name = _frag("OPENROUTER", "_API", "_KEY")
    result = _load_result("PMBOT_SOURCE_003_RESULT.json")
    for path in result["files_changed"]:
        text = (ROOT / path).read_text(encoding="utf-8", errors="ignore")
        assert secret_name not in text, path
