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

## Quality Warnings By Owner

- code: 0
- fixture: 103
- schema: 25
- data: 21
- unknown: 0

## Quality Warnings By Action Type

- fix_required: 123
- review_required: 25
- ignore_allowed: 1

## Top Quality Action Items

- align expected fixture: count=51, owner=fixture, action_type=fix_required, severity=action_required
- create missing actual artifact: count=50, owner=fixture, action_type=fix_required, severity=action_required
- add schema_version to artifact: count=19, owner=schema, action_type=fix_required, severity=action_required
- remove stale embedded pointer: count=15, owner=data, action_type=review_required, severity=review_needed
- remove stale embedded reference: count=6, owner=data, action_type=review_required, severity=review_needed

## Artifact Inventory

- total_artifacts: 20
- present_artifacts: 20
- missing_artifacts: 0
- required_missing_artifacts: 0

- product_001_result: docs/PMBOT_PRODUCT_001_RESULT.json (present=true, required=true, parse_status=parsed)
- integration_008_result: docs/PMBOT_INTEGRATION_008_RESULT.json (present=true, required=true, parse_status=parsed)
- paper_017_result: docs/PMBOT_PAPER_017_RESULT.json (present=true, required=false, parse_status=parsed)
- paper_018_result: docs/PMBOT_PAPER_018_RESULT.json (present=true, required=true, parse_status=parsed)
- paper_019_result: docs/PMBOT_PAPER_019_RESULT.json (present=true, required=false, parse_status=parsed)
- paper_019_multi_market_run_series: pm_bot/paper/multi_market_paper_run_series.v1.json (present=true, required=false, parse_status=parsed)
- paper_020_result: docs/PMBOT_PAPER_020_RESULT.json (present=true, required=false, parse_status=parsed)
- paper_020_paper_run_series_postmortem: pm_bot/paper/paper_run_series_postmortem.v1.json (present=true, required=false, parse_status=parsed)
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

## PAPER-019 Multi-Market Run Series

- section_id: paper_019_multi_market_run_series
- artifact_status: present
- artifact_pointer: pm_bot/paper/multi_market_paper_run_series.v1.json
- artifact_parse_status: parsed
- series_status: series_run_passed
- markets_seen: 5
- records_seen: 5
- records_processed: 4

## PAPER-019 Records By Status

- accepted_accounting_record: 3
- blocked_fixture_record: 1
- manual_review_only: 1

## PAPER-019 Accounting-Only Summary

- paper_accounting_total_records: 4
- paper_accounting_settled_count: 3
- paper_accounting_open_count: 1
- paper_accounting_win_count: 1
- paper_accounting_loss_count: 1
- paper_accounting_flat_count: 1
- paper_accounting_total_cost_basis: 24.00
- paper_accounting_settled_cost_basis: 19.00
- paper_accounting_open_cost_basis: 5.00
- paper_accounting_total_settlement_value: 18.00
- paper_accounting_cumulative_pnl: -1.00
- paper_accounting_average_settled_pnl: -0.33
- paper_accounting_gross_profit: 6.00
- paper_accounting_gross_loss: -7.00
- paper_accounting_max_gain: 6.00
- paper_accounting_max_loss: -7.00

## PAPER-019 Blocked Or Manual Review Summary

- blocked_fixture_record_count: 1
- manual_review_only_count: 1
- blocked_or_rejected_records: 1
- manual_review_only_records: 1
- paper-run-series-record-004: market_id=paper-series-market-open-manual-004, processing_status=manual_review_only, lifecycle_state=open, accounting_included=true
- paper-run-series-record-005: market_id=paper-series-market-blocked-005, processing_status=blocked_fixture_record, lifecycle_state=blocked, accounting_included=false

## PAPER-019 Interpretation Warning

- PAPER-019 values are deterministic fixture/accounting-only outputs and are not strategy profitability, recommendation, EV, edge, probability, or market decision evidence.

## PAPER-019 Safety Counters

- real_orders_created: 0
- autonomous_paper_orders: 0
- network_calls: 0
- commands_executed: 0
- autonomous_decisions: 0

## PAPER-020 Paper Run Series Postmortem

- section_id: paper_020_paper_run_series_postmortem
- artifact_status: present
- artifact_pointer: pm_bot/paper/paper_run_series_postmortem.v1.json
- artifact_parse_status: parsed
- postmortem_status: postmortem_completed
- source_paper_019_found: true
- source_paper_019_series_status: series_run_passed
- markets_seen: 5
- records_seen: 5
- records_processed: 4

## PAPER-020 Accounting-Only PnL Warning

- cumulative_pnl: -1.00
- accounting_only_warning_present: true
- PAPER-019 PnL is accounting-only fixture output, not strategy profitability; it is not a recommendation, edge, EV, probability estimate, market score, or market truth evidence.

## PAPER-020 Record Status Summary

- accepted_accounting_record: count=3, operator_meaning=Record was accepted from the local fixture for accounting summary only.
- manual_review_only: count=1, operator_meaning=Record remains an open manual-review fixture item; it is inert and does not create orders.
- blocked_fixture_record: count=1, operator_meaning=Record was retained as blocked fixture context and excluded from accounting.

## PAPER-020 Fixture Limitations

- The series has five local fixture records and is not statistically representative.
- All accounting values are explicit fixture values; no live settlement truth is inferred.
- Only one open manual-review record and one blocked record are represented.
- No fees, liquidity, orderbook state, slippage, fill uncertainty, or timing variance are modeled.
- The fixture does not validate market discovery, live data handling, wallet access, or execution behavior.

## PAPER-020 Recommended Next Fixture Expansions

- Add more settled fixture records covering additional cost and settlement combinations.
- Add more open manual-review fixture records that remain inert until explicit fixture settlement values exist.
- Add blocked fixture variants for malformed accounting values and unsafe lineage flags.
- Add boundary accounting examples for zero cost, zero settlement, and unusually large fixture values.

## PAPER-020 Safety Counters

- real_orders_created: 0
- autonomous_paper_orders: 0
- network_calls: 0
- commands_executed: 0
- autonomous_decisions: 0

## PAPER-020 Next Safe Action

- PMBOT-WORKBENCH-006-SURFACE-PAPER-020-POSTMORTEM or PMBOT-PRODUCT-002-NEXT-MVP-GATE-REVIEW

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
