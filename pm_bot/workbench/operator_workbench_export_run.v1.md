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
- waiting_for_operator_pasted_response: 0
- blocked_missing_packet: 0
- offline_manual_only: true
- not_truth_source: true
- not_trading_advice: true
- not_execution_authority: true

## Warnings

- none

## Safety Flags

- automation_daemon: false
- autonomous_paper_orders: false
- command_execution: false
- deterministic: true
- local_file_operations_only: true
- manual_cli_only: true
- market_decisions: false
- network_api: false
- offline_only: true
- runtime_wiring: false
- scoring_probability_ev_edge: false
- trading: false
- wallet: false

- next_safe_action: Open pm_bot/workbench/operator_workbench_export_run.v1.md, then pm_bot/workbench/operator_review_pack.v1.md for manual local review.
