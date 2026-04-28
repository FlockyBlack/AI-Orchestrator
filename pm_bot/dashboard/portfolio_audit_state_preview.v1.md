# PMBOT Portfolio Audit State Preview v1

- schema_version: portfolio_audit_state_preview.v1
- dashboard_state_export_version: v2
- generated_by: pm_bot/dashboard/export_portfolio_audit_state.py
- generated_at_policy: deterministic_static_snapshot_no_current_time
- known_market_ids: 824952, series_btc_above_90000_2026_05_31

## Product Stage

- dashboard_scope: PMBOT-DASHBOARD-002-PORTFOLIO-AUDIT-STATE-EXPORT
- dashboard_001_status: completed_with_warnings
- paper_017_status: completed_ready_for_review
- integration_006_verdict: abc_round001_merged_to_main_with_known_fixture_warning
- infra_008_present: true
- infra_008_status: completed_ready_for_review
- infra_008_parse_status: parsed
- current_known_portfolio_audit_status: paper_017_reconciliation_available_with_dashboard_002_static_export

## Portfolio Accounting Summary

- summary_status: portfolio_accounting_state_ready
- accepted_accounting_market_ids: 824952
- paper_accounting_ledger_entries: 1
- paper_accounting_settled_count: 1
- paper_accounting_open_count: 0
- paper_portfolio_snapshot_records: 1
- paper_metrics_report_records: 1
- paper_accounting_cumulative_pnl: 6.00
- paper_accounting_gross_profit: 6.00
- paper_accounting_gross_loss: 0.00

## Existing Audit Summary

- present: true
- audit_status: reconciliation_passed
- checks_total: 14
- checks_passed: 14
- checks_failed: 0
- mismatches_count: 0
- warnings_count: 0

## Future Batch Audit Placeholder

- paper_018_required: false
- paper_018_present: true
- paper_018_status: completed_ready_for_review
- paper_018_parse_status: parsed
- batch_audit_status: None
- batch_ids: (none)

## Artifact Pointers

- dashboard_001_contract: pm_bot/dashboard/dashboard_state_contract.v1.json (present=true)
- dashboard_001_preview_json: pm_bot/dashboard/dashboard_state_preview.v1.json (present=true)
- dashboard_001_preview_markdown: pm_bot/dashboard/dashboard_state_preview.v1.md (present=true)
- dashboard_001_result: docs/PMBOT_DASHBOARD_001_RESULT.json (present=true)
- future_batch_audit_summary_json: pm_bot/paper/paper_batch_audit_summary.v1.json (present=false)
- future_paper_018_result: docs/PMBOT_PAPER_018_RESULT.json (present=true)
- infra_007_result: docs/PMBOT_INFRA_007_RESULT.json (present=true)
- infra_008_result: docs/PMBOT_INFRA_008_RESULT.json (present=true)
- integration_002_result: docs/PMBOT_INTEGRATION_002_RESULT.json (present=true)
- integration_003_result: docs/PMBOT_INTEGRATION_003_RESULT.json (present=true)
- integration_006_result: docs/PMBOT_INTEGRATION_006_RESULT.json (present=true)
- latest_stage_summary: docs/PM_BOT_STAGE_SUMMARY_V55.md (present=true)
- manual_paper_intent_ledger_json: pm_bot/paper/manual_paper_intent_ledger.v1.json (present=true)
- paper_017_expected_reconciliation_audit_json: pm_bot/paper/expected_paper_accounting_reconciliation_audit.v1.json (present=true)
- paper_017_reconciliation_audit_json: pm_bot/paper/paper_accounting_reconciliation_audit.v1.json (present=true)
- paper_017_reconciliation_audit_markdown: pm_bot/paper/paper_accounting_reconciliation_audit.v1.md (present=true)
- paper_017_result: docs/PMBOT_PAPER_017_RESULT.json (present=true)
- paper_accounting_ledger_json: pm_bot/paper/paper_accounting_ledger.v1.json (present=true)
- paper_accounting_pnl_preview_json: pm_bot/paper/paper_accounting_pnl_preview.v1.json (present=true)
- paper_batch_011_013_result: docs/PMBOT_PAPER_BATCH_011_013_RESULT.json (present=true)
- paper_batch_014_016_result: docs/PMBOT_PAPER_BATCH_014_016_RESULT.json (present=true)
- paper_fill_events_json: pm_bot/paper/paper_fill_events.v1.json (present=true)
- paper_metrics_report_json: pm_bot/paper/paper_metrics_report.v1.json (present=true)
- paper_portfolio_snapshot_json: pm_bot/paper/paper_portfolio_snapshot.v1.json (present=true)
- paper_portfolio_state_after_inbox_json: pm_bot/paper/paper_portfolio_state_after_inbox.v1.json (present=true)
- paper_portfolio_state_after_snapshot_json: pm_bot/paper/paper_portfolio_state_after_snapshot.v1.json (present=true)
- paper_portfolio_state_json: pm_bot/paper/paper_portfolio_state.v1.json (present=true)
- portfolio_audit_contract: pm_bot/dashboard/portfolio_audit_state_contract.v1.json (present=true)
- portfolio_audit_expected_preview_json: pm_bot/dashboard/expected_portfolio_audit_state_preview.v1.json (present=true)
- portfolio_audit_preview_json: pm_bot/dashboard/portfolio_audit_state_preview.v1.json (present=true)
- portfolio_audit_preview_markdown: pm_bot/dashboard/portfolio_audit_state_preview.v1.md (present=true)

## Safety

- authenticated_data: false
- autonomous_paper_orders: false
- browser_automation: false
- credentials: false
- dashboard_runtime: false
- frontend: false
- live_trading: false
- market_decisions: false
- network_api: false
- real_orders: false
- recommendations: false
- runtime_wiring: false
- scoring_probability_ev_edge: false
- server: false
- trading: false
- truth_inference: false
- wallet: false

## Interpretation Warnings

- Paper accounting PnL is fixture/manual accounting only and is not strategy profitability.
- Audit pass/fail state reflects deterministic local artifact consistency only, not truth inference.
- This snapshot does not recommend a side, size, price, market, or trade.
- This snapshot does not contain probability estimates, EV, edge, market scoring, live prices, or live fetch results.
- This snapshot reads local artifacts only and does not create executable orders or autonomous paper orders.
- Future batch audit fields are placeholders unless their optional local artifacts are present and integration-reviewed.
