# PMBOT Artifact Health Report v1

- task_id: PMBOT-QUALITY-001-ARTIFACT-HEALTH-AND-STALENESS-CHECK
- schema_version: artifact_health_report.v1
- generated_by: pm_bot/quality/export_artifact_health_report.py
- report_status: health_passed
- artifacts_checked: 228
- artifacts_present_count: 228
- artifacts_missing_count: 0
- json_parse_pass_count: 156
- json_parse_fail_count: 1
- schema_version_missing_count: 4
- task_id_missing_where_expected_count: 0
- status_fields_missing_where_expected_count: 0

## Warning Severity Summary

- total_warnings: 0
- blocking_count: 0
- action_required_count: 0
- review_needed_count: 0
- informational_count: 0
- blocking_warning_detected: false
- operator_summary: No quality warnings detected.
- recommended_manual_action: Continue manual review with no quality warning follow-up required.

## Top Warning Categories

- none

## Warnings By Owner

- code: 0
- fixture: 0
- schema: 0
- data: 0
- unknown: 0

## Warnings By Action Type

- fix_required: 0
- review_required: 0
- ignore_allowed: 0

## Top Action Items

- none

## Warning Severity Model

- blocking: Stop operator review and repair the artifact or safety issue first.
- action_required: Review and resolve or explicitly accept before relying on the package.
- review_needed: Inspect as artifact hygiene context; it does not necessarily block review.
- informational: Low-priority context retained for traceability.

## Documented Exceptions

- total_documented_exceptions: 48
- exceptions_by_type: {"accepted_missing_pointer_target": 20, "documented_legacy_reference": 23, "documented_non_object_json_artifact": 4, "known_intentional_malformed_fixture_parse_failure": 1}

## Embedded Pointer Health

- checked_count: 634
- present_count: 614
- missing_count: 20
- absolute_count: 0

## Expected Fixture Alignment

- checks_total: 72
- aligned_count: 72
- mismatch_count: 0
- actual_missing_count: 0

## Safety Flags

- autonomous_paper_orders: false
- command_execution: false
- market_decisions: false
- network_api: false
- runtime_wiring: false
- scoring_probability_ev_edge: false
- trading: false
- wallet: false

## Warnings

- none

## Artifacts

- docs/PMBOT_DASHBOARD_002_RESULT.json: exists=true, json_parse_status=parsed, schema_version=pmbot_dashboard_002_result.v1, warnings=0
- docs/PMBOT_INFRA_009_RESULT.json: exists=true, json_parse_status=parsed, schema_version=pmbot_infra_009_result.v1, warnings=0
- docs/PMBOT_INTEGRATION_008_RESULT.json: exists=true, json_parse_status=parsed, schema_version=pmbot_integration_008_result.v1, warnings=0
- docs/PMBOT_OPERATOR_002_RESULT.json: exists=true, json_parse_status=parsed, schema_version=pmbot_operator_002_result.v1, warnings=0
- docs/PMBOT_PAPER_018_RESULT.json: exists=true, json_parse_status=parsed, schema_version=pmbot_paper_018_result.v1, warnings=0
- docs/PMBOT_PRODUCT_001_RESULT.json: exists=true, json_parse_status=parsed, schema_version=pmbot_product_001_result.v1, warnings=0
- pm_bot/dashboard/dashboard_state_contract.v1.json: exists=true, json_parse_status=parsed, schema_version=dashboard_state_contract.v1, warnings=0
- pm_bot/dashboard/dashboard_state_preview.v1.json: exists=true, json_parse_status=parsed, schema_version=dashboard_state_preview.v1, warnings=0
- pm_bot/dashboard/dashboard_state_preview.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/dashboard/expected_dashboard_state_preview.v1.json: exists=true, json_parse_status=parsed, schema_version=dashboard_state_preview.v1, warnings=0
- pm_bot/dashboard/expected_portfolio_audit_state_preview.v1.json: exists=true, json_parse_status=parsed, schema_version=portfolio_audit_state_preview.v1, warnings=0
- pm_bot/dashboard/expected_static_operator_report_summary.v1.json: exists=true, json_parse_status=parsed, schema_version=static_operator_report_summary.v1, warnings=0
- pm_bot/dashboard/portfolio_audit_state_contract.v1.json: exists=true, json_parse_status=parsed, schema_version=portfolio_audit_state_contract.v1, warnings=0
- pm_bot/dashboard/portfolio_audit_state_preview.v1.json: exists=true, json_parse_status=parsed, schema_version=portfolio_audit_state_preview.v1, warnings=0
- pm_bot/dashboard/portfolio_audit_state_preview.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/dashboard/static_operator_report_summary.v1.json: exists=true, json_parse_status=parsed, schema_version=static_operator_report_summary.v1, warnings=0
- pm_bot/operator/expected_manual_command_inbox_review.v1.json: exists=true, json_parse_status=parsed, schema_version=manual_command_inbox_review.v1, warnings=0
- pm_bot/operator/expected_operator_review_bundle.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/operator/expected_operator_review_bundle.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/operator/expected_operator_review_checklist.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/operator/expected_operator_review_checklist.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/operator/expected_paper_candidate_review_table.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/operator/expected_paper_candidate_review_table.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/operator/expected_risk_audit_summary.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/operator/expected_risk_audit_summary.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/operator/expected_watchlist_policy_report.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/operator/expected_watchlist_policy_report.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/operator/manual_command_contract.v1.json: exists=true, json_parse_status=parsed, schema_version=manual_command_contract.v1, warnings=0
- pm_bot/operator/manual_command_examples.v1.json: exists=true, json_parse_status=parsed, schema_version=manual_command_examples.v1, warnings=0
- pm_bot/operator/manual_command_examples.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/operator/manual_command_inbox_fixture.v1.json: exists=true, json_parse_status=parsed, schema_version=manual_command_inbox_fixture.v1, warnings=0
- pm_bot/operator/manual_command_inbox_review.v1.json: exists=true, json_parse_status=parsed, schema_version=manual_command_inbox_review.v1, warnings=0
- pm_bot/operator/manual_command_inbox_review.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/operator/operator_review_bundle.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/operator/operator_review_bundle.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/operator/operator_review_checklist.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/operator/operator_review_checklist.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/operator/paper_candidate_review_table.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/operator/paper_candidate_review_table.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/operator/review_pack_command_bridge_contract.v1.json: exists=true, json_parse_status=parsed, schema_version=review_pack_command_bridge_contract.v1, warnings=0
- pm_bot/operator/review_pack_command_bridge_examples.v1.json: exists=true, json_parse_status=parsed, schema_version=review_pack_command_bridge_examples.v1, warnings=0
- pm_bot/operator/review_pack_command_bridge_examples.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/operator/risk_audit_summary.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/operator/risk_audit_summary.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/operator/watchlist_policy_report.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/operator/watchlist_policy_report.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/crypto_numeric_execution_fixture.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/crypto_numeric_lifecycle_regression_gates.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/crypto_numeric_lifecycle_regression_gates.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/crypto_numeric_lifecycle_replay.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/crypto_numeric_lifecycle_replay.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/crypto_numeric_lifecycle_replay_cases.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/crypto_numeric_paper_execution_ledger.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/crypto_numeric_paper_execution_ledger.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/crypto_numeric_paper_lifecycle.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/crypto_numeric_paper_lifecycle.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/crypto_threshold_hit_policy_scenarios.v1.json: exists=true, json_parse_status=parsed, schema_version=threshold_hit_policy_scenario_results.v1, warnings=0
- pm_bot/paper/crypto_threshold_hit_policy_scenarios.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/crypto_threshold_hit_review_table.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/crypto_threshold_hit_review_table.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/crypto_threshold_hit_triage_report.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/crypto_threshold_hit_triage_report.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_crypto_numeric_lifecycle_regression_gates.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_crypto_numeric_lifecycle_regression_gates.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_crypto_numeric_lifecycle_replay.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_crypto_numeric_lifecycle_replay.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_crypto_numeric_paper_execution_ledger.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_crypto_numeric_paper_execution_ledger.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_crypto_numeric_paper_lifecycle.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_crypto_numeric_paper_lifecycle.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_crypto_threshold_hit_policy_scenarios.v1.json: exists=true, json_parse_status=parsed, schema_version=threshold_hit_policy_scenario_results.v1, warnings=0
- pm_bot/paper/expected_crypto_threshold_hit_policy_scenarios.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_crypto_threshold_hit_review_table.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_crypto_threshold_hit_review_table.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_crypto_threshold_hit_triage_report.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_crypto_threshold_hit_triage_report.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_final_dossier_paper_readiness_result.v1.json: exists=true, json_parse_status=parsed, schema_version=final_dossier_paper_readiness_result.v1, warnings=0
- pm_bot/paper/expected_live_shaped_snapshot_paper_lifecycle.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_live_shaped_snapshot_paper_lifecycle.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_local_snapshot_inbox_paper_portfolio.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_local_snapshot_inbox_paper_portfolio.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_local_snapshot_inbox_run_ledger.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_local_snapshot_paper_portfolio_state.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_local_snapshot_paper_portfolio_state.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_local_snapshot_series_paper_portfolio.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_local_snapshot_series_paper_portfolio.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_local_snapshot_series_risk_scenarios.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_local_snapshot_series_risk_scenarios.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_manual_paper_inbox_bundle.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_manual_paper_inbox_bundle_summary.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_manual_paper_operator_cycle.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_manual_paper_operator_cycle.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_manual_paper_operator_cycle_manifest.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_manual_paper_operator_cycle_threshold_hit_review.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_manual_paper_operator_cycle_threshold_hit_review.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_manual_paper_workspace.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_manual_paper_workspace_quarantine.v1.json: exists=true, json_parse_status=parsed, schema_version=None, warnings=0
- pm_bot/paper/expected_manual_paper_workspace_summary.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_manual_snapshot_import_manifest.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_manual_snapshot_workspace_import.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_manual_snapshot_workspace_import.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/expected_multi_market_paper_run_series.v1.json: exists=true, json_parse_status=parsed, schema_version=multi_market_paper_run_series.v1, warnings=0
- pm_bot/paper/expected_paper_accounting_batch_audit.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_accounting_batch_audit.v1, warnings=0
- pm_bot/paper/expected_paper_accounting_ledger.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_accounting_ledger.v1, warnings=0
- pm_bot/paper/expected_paper_accounting_pnl_preview.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_accounting_pnl_preview.v1, warnings=0
- pm_bot/paper/expected_paper_accounting_reconciliation_audit.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_accounting_reconciliation_audit.v1, warnings=0
- pm_bot/paper/expected_paper_batch_audit_summary.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_batch_audit_summary.v1, warnings=0
- pm_bot/paper/expected_paper_decision_policy_spec.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_decision_policy_spec.v1, warnings=0
- pm_bot/paper/expected_paper_decision_simulation_gate.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_decision_simulation_gate.v1, warnings=0
- pm_bot/paper/expected_paper_decision_simulation_preview.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_decision_simulation_preview.v1, warnings=0
- pm_bot/paper/expected_paper_fill_events.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_fill_events.v1, warnings=0
- pm_bot/paper/expected_paper_metrics_report.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_metrics_report.v1, warnings=0
- pm_bot/paper/expected_paper_policy_review_result.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_policy_review_result.v1, warnings=0
- pm_bot/paper/expected_paper_portfolio_snapshot.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_portfolio_snapshot.v1, warnings=0
- pm_bot/paper/expected_paper_run_series_postmortem.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_run_series_postmortem.v1, warnings=0
- pm_bot/paper/expected_paper_simulation.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_paper_simulation_plan_draft.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_simulation_plan_draft.v1, warnings=0
- pm_bot/paper/expected_paper_workbench_preview.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_workbench_preview.v1, warnings=0
- pm_bot/paper/expected_real_market_triage_report.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/expected_real_market_triage_report.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/final_dossier_paper_readiness_report.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/final_dossier_paper_readiness_result.v1.json: exists=true, json_parse_status=parsed, schema_version=final_dossier_paper_readiness_result.v1, warnings=0
- pm_bot/paper/fixtures/polymarket_markets_active_threshold_hit.fixture.json: exists=true, json_parse_status=parsed, schema_version=None, warnings=0
- pm_bot/paper/live_shaped_snapshot_paper_lifecycle.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/live_shaped_snapshot_paper_lifecycle.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/local_snapshot_inbox/001_series_snapshot_001.json: exists=true, json_parse_status=parsed, schema_version=local_snapshot_series_fixture.v1, warnings=0
- pm_bot/paper/local_snapshot_inbox/002_series_snapshot_002.json: exists=true, json_parse_status=parsed, schema_version=local_snapshot_series_fixture.v1, warnings=0
- pm_bot/paper/local_snapshot_inbox/003_series_snapshot_003.json: exists=true, json_parse_status=parsed, schema_version=local_snapshot_series_fixture.v1, warnings=0
- pm_bot/paper/local_snapshot_inbox_paper_portfolio.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/local_snapshot_inbox_paper_portfolio.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/local_snapshot_inbox_run_ledger.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/local_snapshot_paper_portfolio_state.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/local_snapshot_paper_portfolio_state.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/local_snapshot_series_fixture.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/local_snapshot_series_paper_portfolio.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/local_snapshot_series_paper_portfolio.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/local_snapshot_series_risk_scenarios.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/local_snapshot_series_risk_scenarios.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/local_snapshot_series_risk_scenarios_source.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/manual_paper_inbox_bundle.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/manual_paper_inbox_bundle_summary.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/manual_paper_intent_ledger.v1.json: exists=true, json_parse_status=parsed, schema_version=manual_paper_intent_ledger.v1, warnings=0
- pm_bot/paper/manual_paper_intent_report.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/manual_paper_intent_template.v1.json: exists=true, json_parse_status=parsed, schema_version=manual_paper_intent_template.v1, warnings=0
- pm_bot/paper/manual_paper_intents_accepted.v1.json: exists=true, json_parse_status=parsed, schema_version=manual_paper_intents_accepted.v1, warnings=0
- pm_bot/paper/manual_paper_intents_input.v1.json: exists=true, json_parse_status=parsed, schema_version=manual_paper_intents_input.v1, warnings=0
- pm_bot/paper/manual_paper_intents_rejected.v1.json: exists=true, json_parse_status=parsed, schema_version=manual_paper_intents_rejected.v1, warnings=0
- pm_bot/paper/manual_paper_operator_cycle.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/manual_paper_operator_cycle.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/manual_paper_operator_cycle_manifest.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/manual_paper_operator_cycle_threshold_hit_review.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/manual_paper_operator_cycle_threshold_hit_review.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/manual_paper_run_fixture_output/run_ledger.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/manual_paper_run_fixture_output/run_summary.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/manual_paper_run_fixture_output/state_after.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/manual_paper_workspace.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/manual_paper_workspace/inbox/001_series_snapshot_001.json: exists=true, json_parse_status=parsed, schema_version=local_snapshot_series_fixture.v1, warnings=0
- pm_bot/paper/manual_paper_workspace/inbox/002_series_snapshot_002.json: exists=true, json_parse_status=parsed, schema_version=local_snapshot_series_fixture.v1, warnings=0
- pm_bot/paper/manual_paper_workspace/inbox/003_series_snapshot_003.json: exists=true, json_parse_status=parsed, schema_version=local_snapshot_series_fixture.v1, warnings=0
- pm_bot/paper/manual_paper_workspace/state/current_state.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/manual_paper_workspace_quarantine.v1.json: exists=true, json_parse_status=parsed, schema_version=None, warnings=0
- pm_bot/paper/manual_paper_workspace_summary.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/manual_snapshot_import_manifest.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/manual_snapshot_import_source/001_series_snapshot_004.json: exists=true, json_parse_status=parsed, schema_version=manual_snapshot_import_source.v1, warnings=0
- pm_bot/paper/manual_snapshot_import_source/002_series_snapshot_005.json: exists=true, json_parse_status=parsed, schema_version=manual_snapshot_import_source.v1, warnings=0
- pm_bot/paper/manual_snapshot_import_source/003_duplicate_series_snapshot_004.json: exists=true, json_parse_status=parsed, schema_version=manual_snapshot_import_source.v1, warnings=0
- pm_bot/paper/manual_snapshot_import_source/004_already_present_series_snapshot_002.json: exists=true, json_parse_status=parsed, schema_version=manual_snapshot_import_source.v1, warnings=0
- pm_bot/paper/manual_snapshot_import_source/005_malformed.json: exists=true, json_parse_status=parse_failed, schema_version=None, warnings=0
- pm_bot/paper/manual_snapshot_import_source/006_unsupported.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/manual_snapshot_import_source/008_polymarket_markets_active_minimized.fixture.json: exists=true, json_parse_status=parsed, schema_version=None, warnings=0
- pm_bot/paper/manual_snapshot_workspace_import.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/manual_snapshot_workspace_import.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/multi_market_paper_run_series.v1.json: exists=true, json_parse_status=parsed, schema_version=multi_market_paper_run_series.v1, warnings=0
- pm_bot/paper/multi_market_paper_run_series.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_accounting_batch_audit.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_accounting_batch_audit.v1, warnings=0
- pm_bot/paper/paper_accounting_batch_audit.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_accounting_ledger.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_accounting_ledger.v1, warnings=0
- pm_bot/paper/paper_accounting_ledger.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_accounting_pnl_preview.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_accounting_pnl_preview.v1, warnings=0
- pm_bot/paper/paper_accounting_pnl_preview.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_accounting_reconciliation_audit.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_accounting_reconciliation_audit.v1, warnings=0
- pm_bot/paper/paper_accounting_reconciliation_audit.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_batch_audit_summary.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_batch_audit_summary.v1, warnings=0
- pm_bot/paper/paper_decision_policy_spec.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_decision_policy_spec.v1, warnings=0
- pm_bot/paper/paper_decision_policy_spec.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_decision_simulation_gate.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_decision_simulation_gate.v1, warnings=0
- pm_bot/paper/paper_decision_simulation_gate.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_decision_simulation_preview.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_decision_simulation_preview.v1, warnings=0
- pm_bot/paper/paper_decision_simulation_preview.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_fill_events.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_fill_events.v1, warnings=0
- pm_bot/paper/paper_fill_events_report.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_fill_source_contract.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_fill_source_contract.v1, warnings=0
- pm_bot/paper/paper_fill_source_fixture.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_fill_source_fixture.v1, warnings=0
- pm_bot/paper/paper_fill_source_report.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_fill_sources_accepted.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_fill_sources_accepted.v1, warnings=0
- pm_bot/paper/paper_fill_sources_rejected.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_fill_sources_rejected.v1, warnings=0
- pm_bot/paper/paper_metrics_report.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_metrics_report.v1, warnings=0
- pm_bot/paper/paper_metrics_report.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_plan_fixture.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_plan_fixture.v1, warnings=0
- pm_bot/paper/paper_policy_review_records_fixture.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_policy_review_records_fixture.v1, warnings=0
- pm_bot/paper/paper_policy_review_report.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_policy_review_result.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_policy_review_result.v1, warnings=0
- pm_bot/paper/paper_portfolio_snapshot.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_portfolio_snapshot.v1, warnings=0
- pm_bot/paper/paper_portfolio_snapshot.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_portfolio_state.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/paper_portfolio_state_after_inbox.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/paper_portfolio_state_after_snapshot.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/paper_run_series_fixture.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_run_series_fixture.v1, warnings=0
- pm_bot/paper/paper_run_series_postmortem.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_run_series_postmortem.v1, warnings=0
- pm_bot/paper/paper_run_series_postmortem.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_settlement_source_fixture.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_settlement_source_fixture.v1, warnings=0
- pm_bot/paper/paper_settlement_sources_accepted.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_settlement_sources_accepted.v1, warnings=0
- pm_bot/paper/paper_settlement_sources_rejected.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_settlement_sources_rejected.v1, warnings=0
- pm_bot/paper/paper_simulation.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/paper_simulation_gate_human_review_records_accepted.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_simulation_gate_human_review_records_accepted.v1, warnings=0
- pm_bot/paper/paper_simulation_gate_human_review_records_input.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_simulation_gate_human_review_records_input.v1, warnings=0
- pm_bot/paper/paper_simulation_gate_human_review_records_rejected.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_simulation_gate_human_review_records_rejected.v1, warnings=0
- pm_bot/paper/paper_simulation_gate_human_review_records_report.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_simulation_plan_draft.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_simulation_plan_draft.v1, warnings=0
- pm_bot/paper/paper_simulation_plan_draft.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/paper_workbench_preview.v1.json: exists=true, json_parse_status=parsed, schema_version=paper_workbench_preview.v1, warnings=0
- pm_bot/paper/paper_workbench_preview.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/portfolio_risk_limits.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/real_market_triage_report.v1.json: exists=true, json_parse_status=parsed, schema_version=v1, warnings=0
- pm_bot/paper/real_market_triage_report.v1.md: exists=true, json_parse_status=not_json, schema_version=None, warnings=0
- pm_bot/paper/threshold_hit_decision_policy.v1.json: exists=true, json_parse_status=parsed, schema_version=threshold_hit_decision_policy.v1, warnings=0
- pm_bot/paper/threshold_hit_policy_scenarios.v1.json: exists=true, json_parse_status=parsed, schema_version=threshold_hit_policy_scenarios.v1, warnings=0
- pm_bot/paper/threshold_hit_reference_context.v1.json: exists=true, json_parse_status=parsed, schema_version=threshold_hit_reference_context.v1, warnings=0
