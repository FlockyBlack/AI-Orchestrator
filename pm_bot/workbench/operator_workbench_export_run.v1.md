# PMBOT Operator Workbench Export Run v1

- schema_version: operator_workbench_export_run.v1
- task_id: PMBOT-WORKBENCH-003-SINGLE-COMMAND-LOCAL-EXPORT
- generated_by: pm_bot/workbench/run_operator_workbench_export.py
- run_mode: manual_local_export
- required_steps_passed: true
- optional_steps_skipped: 0
- network_calls: 0
- commands_executed: 0
- orders_created: 0

## Steps

- portfolio_audit_state: status=ran, required=false, script=pm_bot/dashboard/export_portfolio_audit_state.py
  output: pm_bot/dashboard/portfolio_audit_state_contract.v1.json
  output: pm_bot/dashboard/portfolio_audit_state_preview.v1.json
  output: pm_bot/dashboard/portfolio_audit_state_preview.v1.md
  output: pm_bot/dashboard/expected_portfolio_audit_state_preview.v1.json
- manual_command_inbox_review: status=ran, required=false, script=pm_bot/operator/review_manual_command_inbox.py
  output: pm_bot/operator/manual_command_inbox_review.v1.json
  output: pm_bot/operator/manual_command_inbox_review.v1.md
  output: pm_bot/operator/expected_manual_command_inbox_review.v1.json
- artifact_health_report: status=ran, required=false, script=pm_bot/quality/export_artifact_health_report.py
  output: pm_bot/quality/artifact_health_report.v1.json
  output: pm_bot/quality/artifact_health_report.v1.md
  output: pm_bot/quality/expected_artifact_health_report.v1.json
  output: docs/PMBOT_QUALITY_001_RESULT.json
  output: docs/PMBOT_CODEX_B_ROUND003_RESULT.json
- openrouter_passive_surface_pointer: status=ran, required=false, script=pm_bot/workbench/openrouter_passive_surface_pointer.py
  output: pm_bot/workbench/openrouter_passive_surface_pointer.v1.json
  output: pm_bot/workbench/openrouter_passive_surface_pointer.v1.md
- operator_openrouter_review_dashboard: status=ran, required=false, script=pm_bot/workbench/operator_openrouter_review_dashboard.py
  output: pm_bot/workbench/operator_openrouter_review_dashboard.v1.json
  output: pm_bot/workbench/operator_openrouter_review_dashboard.v1.md
- operator_review_pack: status=ran, required=true, script=pm_bot/workbench/export_operator_review_pack.py
  output: pm_bot/workbench/operator_review_pack.v1.json
  output: pm_bot/workbench/operator_review_pack.v1.md
  output: pm_bot/workbench/expected_operator_review_pack.v1.json
  output: docs/PMBOT_WORKBENCH_001_RESULT.json
  output: docs/PMBOT_CODEX_A_ROUND003_RESULT.json

## Artifacts Refreshed

- pm_bot/dashboard/portfolio_audit_state_contract.v1.json
- pm_bot/dashboard/portfolio_audit_state_preview.v1.json
- pm_bot/dashboard/portfolio_audit_state_preview.v1.md
- pm_bot/dashboard/expected_portfolio_audit_state_preview.v1.json
- pm_bot/operator/manual_command_inbox_review.v1.json
- pm_bot/operator/manual_command_inbox_review.v1.md
- pm_bot/operator/expected_manual_command_inbox_review.v1.json
- pm_bot/quality/artifact_health_report.v1.json
- pm_bot/quality/artifact_health_report.v1.md
- pm_bot/quality/expected_artifact_health_report.v1.json
- docs/PMBOT_QUALITY_001_RESULT.json
- docs/PMBOT_CODEX_B_ROUND003_RESULT.json
- pm_bot/workbench/openrouter_passive_surface_pointer.v1.json
- pm_bot/workbench/openrouter_passive_surface_pointer.v1.md
- pm_bot/workbench/operator_openrouter_review_dashboard.v1.json
- pm_bot/workbench/operator_openrouter_review_dashboard.v1.md
- pm_bot/workbench/operator_review_pack.v1.json
- pm_bot/workbench/operator_review_pack.v1.md
- pm_bot/workbench/expected_operator_review_pack.v1.json
- docs/PMBOT_WORKBENCH_001_RESULT.json
- docs/PMBOT_CODEX_A_ROUND003_RESULT.json
- pm_bot/workbench/operator_workbench_export_run.v1.json
- pm_bot/workbench/operator_workbench_export_run.v1.md
- pm_bot/workbench/expected_operator_workbench_export_run.v1.json
- docs/PMBOT_WORKBENCH_003_RESULT.json

## Actual Manual LLM Response Trial

- artifact_path: pm_bot/llm/actual_manual_llm_response_trial.v1.json
- artifact_present: true
- operator_response_path: pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json
- operator_response_present: true
- response_source_type: actual_operator_pasted_response
- market_id: 824952
- source_artifact_path: pm_bot/research/selected_ingest_final_dossier_drafts.v1.json
- run_status: actual_response_accepted
- acceptance_status: accepted_for_operator_review
- response_validation_status: accepted
- manual_review_status: accepted
- quality_gate_status: quality_passed
- errors_count: 0
- warnings_count: 0
- next_safe_operator_action: Review the accepted local artifacts as offline operator context only; do not execute or automate anything.
- explicit_warning: This surface is offline review context only. It is not a truth source, not trading advice, and not execution authority.

## Manual LLM Review Queue

- artifact_path: pm_bot/llm/manual_llm_review_queue.v1.json
- artifact_present: true
- queue_items_total: 15
- response_accepted_for_operator_review: 1
- waiting_for_operator_pasted_response: 14
- blocked_missing_packet: 0
- offline_manual_only: true
- not_truth_source: true
- not_trading_advice: true
- not_execution_authority: true

## OpenRouter Passive Surface

- artifact_path: pm_bot/workbench/openrouter_passive_surface_pointer.v1.json
- status: passive_surface_pointer_ready
- source_batch_task: PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL
- source_baseline_task: PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY
- source_surface_task: PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-AND-WORKBENCH-N5-INTEGRATION
- source_048_status: completed_pushed
- source_052_status: completed_pushed
- surfaced_market_ids: 569344, 569366, 569368, 569373, 573656
- model: anthropic/claude-sonnet-4.5
- total_calls: 5
- accepted_for_operator_review_count: 5
- blocked_count: 0
- fenced_response_count: 5
- normalized_response_count: 5
- clean_raw_json_response_count: 0
- operator_review_only: true
- passive_context_only: true
- no_trading_authority: true
- no_queue_authority: true
- no_runtime_authority: true
- no_dispatcher_authority: true
- no_wallet_or_order_authority: true
- acceptance_is_not_trading_approval: true
- analysis_only: true
- manual_review_only: true

## OpenRouter Review Dashboard

- artifact_path: pm_bot/workbench/operator_openrouter_review_dashboard.v1.json
- status: operator_openrouter_review_dashboard_created
- latest_surface: PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-AND-WORKBENCH-N5-INTEGRATION
- latest_baseline: PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY
- latest_workbench_integration_status: multi_batch_passive_surface_pointer_ready
- combined_cost: 0.325071
- combined_tokens: 48573
- total_markets_found: 14
- evidence_readiness_integration_status: source_001_context_ready
- evidence_readiness_low_count: 4
- average_evidence_readiness_score: 75.43
- markets_with_medium_evidence_completeness: 563650, 569332, 569333, 569334, 569343, 569344, 569366, 569368, 569373, 573656
- recommended_next_local_enrichment_focus: resolution source extraction, source gap normalization, operator checklist standardization for unreviewed packets, contradiction and risk context builder for unreviewed packets, local packet completeness scorer integration
- no_market_action_guidance: true

## Warnings

- none

## Safety Flags

- acceptance_is_not_trading_approval: true
- analysis_only: true
- automation_daemon: false
- autonomous_paper_orders: false
- command_execution: false
- deterministic: true
- local_file_operations_only: true
- manual_cli_only: true
- manual_review_only: true
- market_decisions: false
- network_api: false
- no_dispatcher_authority: true
- no_queue_authority: true
- no_runtime_authority: true
- no_trading_authority: true
- no_wallet_or_order_authority: true
- offline_only: true
- operator_review_only: true
- passive_context_only: true
- runtime_wiring: false
- scoring_probability_ev_edge: false
- trading: false
- wallet: false

- next_safe_action: Open pm_bot/workbench/operator_workbench_export_run.v1.md, then pm_bot/workbench/operator_review_pack.v1.md for manual local review.
