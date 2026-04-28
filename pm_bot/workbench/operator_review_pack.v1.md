# PMBOT Operator Review Pack v1

- schema_version: operator_review_pack.v1
- generated_by: pm_bot/workbench/export_operator_review_pack.py
- generated_at_policy: deterministic_static_snapshot_no_current_time
- product_direction: operator_workbench_review_pack_v1
- paper_orders_created: 0
- commands_executed: 0
- network_calls: 0

## Quality Warning Summary

- quality_report_status: health_passed_with_warnings
- total_warnings: 149
- blocking_warnings: 0
- action_required_warnings: 123
- review_needed_warnings: 25
- informational_warnings: 1
- blocking_warning_detected: false
- operator_summary: No blocking warnings detected; review action_required categories before relying on the package.
- recommended_manual_action: Review action_required warning categories first, then inspect review_needed and informational categories.

## Quality Warning Interpretation

- blocking: blocking means stop and repair before relying on the package.
- action_required: action_required means review before relying on the package.
- review_needed: review_needed means inspect but not necessarily block.
- informational: informational means low-priority context.

## Top Quality Warning Categories

- expected_fixture_alignment_warning: count=51, severity=action_required, bucket=artifact has an expected fixture alignment warning
- fixture_alignment_actual_missing: count=50, severity=action_required, bucket=expected fixture exists but actual artifact is missing
- schema_version_missing: count=19, severity=action_required, bucket=schema version metadata missing
- embedded_artifact_pointer_warning: count=15, severity=review_needed, bucket=embedded artifact pointer needs inspection
- stale_reference_warning: count=6, severity=review_needed, bucket=historical or stale reference needs inspection

## Artifact Inventory

- total_artifacts: 16
- present_artifacts: 16
- missing_artifacts: 0
- required_missing_artifacts: 0

- product_001_result: docs/PMBOT_PRODUCT_001_RESULT.json (present=true, required=true, parse_status=parsed)
- integration_008_result: docs/PMBOT_INTEGRATION_008_RESULT.json (present=true, required=true, parse_status=parsed)
- paper_017_result: docs/PMBOT_PAPER_017_RESULT.json (present=true, required=false, parse_status=parsed)
- paper_018_result: docs/PMBOT_PAPER_018_RESULT.json (present=true, required=true, parse_status=parsed)
- dashboard_002_result: docs/PMBOT_DASHBOARD_002_RESULT.json (present=true, required=true, parse_status=parsed)
- operator_002_result: docs/PMBOT_OPERATOR_002_RESULT.json (present=true, required=true, parse_status=parsed)
- infra_009_result: docs/PMBOT_INFRA_009_RESULT.json (present=true, required=false, parse_status=parsed)
- infra_009_report: docs/PMBOT_INFRA_009_ABC_ROUND003_WORKTREE_MATERIALIZATION.md (present=true, required=false, parse_status=not_applicable)
- paper_accounting_reconciliation_audit: pm_bot/paper/paper_accounting_reconciliation_audit.v1.json (present=true, required=true, parse_status=parsed)
- paper_accounting_batch_audit: pm_bot/paper/paper_accounting_batch_audit.v1.json (present=true, required=true, parse_status=parsed)
- paper_accounting_ledger: pm_bot/paper/paper_accounting_ledger.v1.json (present=true, required=true, parse_status=parsed)
- paper_accounting_pnl_preview: pm_bot/paper/paper_accounting_pnl_preview.v1.json (present=true, required=true, parse_status=parsed)
- paper_portfolio_snapshot: pm_bot/paper/paper_portfolio_snapshot.v1.json (present=true, required=true, parse_status=parsed)
- paper_metrics_report: pm_bot/paper/paper_metrics_report.v1.json (present=true, required=true, parse_status=parsed)
- portfolio_audit_state_preview: pm_bot/dashboard/portfolio_audit_state_preview.v1.json (present=true, required=true, parse_status=parsed)
- manual_command_inbox_review: pm_bot/operator/manual_command_inbox_review.v1.json (present=true, required=true, parse_status=parsed)

## Paper Audits

- reconciliation_audit_status: reconciliation_passed
- reconciliation_checks_passed: 14
- batch_audit_status: batch_audit_passed
- batch_records_audited: 3
- batch_checks_passed: 13
- audit_warnings_count: 0
- audit_mismatches_count: 0

## Portfolio Accounting

- summary_status: portfolio_accounting_state_ready
- accepted_accounting_market_ids: 824952
- paper_accounting_cumulative_pnl: 6.00
- batch_accounting_cumulative_pnl: -1.00
- accounting_boundary_warning: Paper accounting PnL is fixture/manual accounting only and is not strategy profitability.

## Dashboard State

- present: true
- schema_version: portfolio_audit_state_preview.v1
- dashboard_state_export_version: v2
- known_market_ids: 824952, series_btc_above_90000_2026_05_31
- current_known_portfolio_audit_status: paper_017_reconciliation_available_with_dashboard_002_static_export

## Operator Inbox

- records_seen: 7
- accepted_count: 3
- rejected_count: 3
- needs_human_review_count: 1
- execution_authority: false
- commands_executed: 0
- network_calls: 0

## Missing Artifacts

- none

## Warnings

- accounting_only_interpretation: Paper accounting PnL is fixture/manual accounting only and is not strategy profitability.
- audit_status_not_truth_inference: Audit pass/fail state reflects deterministic local artifact consistency only, not truth inference.
- no_recommendations_or_decisions: This operator review pack does not recommend markets, sides, prices, sizes, orders, trades, paper orders, or decisions.
- local_artifacts_only: This pack reads local artifacts only and contains no live prices, live fetch results, or API results.

## Safety Flags

- autonomous_paper_orders: false
- command_execution: false
- credentials: false
- deterministic_output: true
- dispatcher_run_codex_changes: false
- live_trading: false
- local_file_reads_only: true
- market_decisions: false
- network_api: false
- offline_only: true
- operator_review_only: true
- real_orders: false
- recommendations: false
- runtime_wiring: false
- scoring_probability_ev_edge: false
- trading: false
- truth_inference: false
- wallet: false

## Next Safe Manual Actions

- review_pack_inventory_and_warnings: Review artifact_inventory, missing_artifacts, and warnings in this local pack.
- review_paper_accounting_audit_artifacts: Inspect the existing paper reconciliation and batch audit artifacts for local consistency status.
- review_operator_inbox_queue: Review accepted, rejected, and needs-human-review inbox records without executing commands.
- integration_review_only: Use this pack as a static input for human integration review only.

- This operator review pack does not recommend markets, sides, prices, sizes, orders, trades, paper orders, or decisions.
