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
