# PMBOT Dashboard State Preview v1

- schema_version: dashboard_state_preview.v1
- generated_by: pm_bot/dashboard/export_dashboard_state_contract.py
- generated_at_policy: deterministic_static_snapshot_no_current_time
- market_ids: 824952

## Product Stage

- dashboard_scope: PMBOT-DASHBOARD-001-DASHBOARD-STATE-EXPORT-CONTRACT
- current_known_paper_status: paper_portfolio_metrics_accepted_for_git_readiness_stage
- integration_003_verdict: accepted_for_git_readiness_stage

## Paper Accounting Summary

- ledger_status: paper_accounting_ledger_history_ready
- portfolio_status: paper_portfolio_snapshot_ready
- metrics_report_status: paper_metrics_report_ready
- paper_accounting_total_records: 1
- paper_accounting_settled_count: 1
- paper_accounting_open_count: 0
- paper_accounting_cumulative_pnl: 6.00
- paper_accounting_gross_profit: 6.00
- paper_accounting_gross_loss: 0.00

## Artifact Pointers

- abc_round_plan: docs/PMBOT_INFRA_005_ABC_PARALLEL_FEATURE_ROUND_PLAN.md (present=true)
- abc_round_result_contract: docs/PMBOT_INFRA_005_CODEX_PARALLEL_RESULT_CONTRACT.v1.json (present=true)
- dashboard_contract: pm_bot/dashboard/dashboard_state_contract.v1.json (present=true)
- dashboard_expected_preview_json: pm_bot/dashboard/expected_dashboard_state_preview.v1.json (present=true)
- dashboard_preview_json: pm_bot/dashboard/dashboard_state_preview.v1.json (present=true)
- dashboard_preview_markdown: pm_bot/dashboard/dashboard_state_preview.v1.md (present=true)
- integration_002_result: docs/PMBOT_INTEGRATION_002_RESULT.json (present=true)
- integration_003_result: docs/PMBOT_INTEGRATION_003_RESULT.json (present=true)
- latest_stage_summary: docs/PM_BOT_STAGE_SUMMARY_V55.md (present=true)
- manual_paper_intent_ledger_json: pm_bot/paper/manual_paper_intent_ledger.v1.json (present=true)
- paper_accounting_ledger_json: pm_bot/paper/paper_accounting_ledger.v1.json (present=true)
- paper_accounting_pnl_preview_json: pm_bot/paper/paper_accounting_pnl_preview.v1.json (present=true)
- paper_batch_011_013_result: docs/PMBOT_PAPER_BATCH_011_013_RESULT.json (present=true)
- paper_batch_014_016_result: docs/PMBOT_PAPER_BATCH_014_016_RESULT.json (present=true)
- paper_fill_events_json: pm_bot/paper/paper_fill_events.v1.json (present=true)
- paper_metrics_report_json: pm_bot/paper/paper_metrics_report.v1.json (present=true)
- paper_portfolio_snapshot_json: pm_bot/paper/paper_portfolio_snapshot.v1.json (present=true)

## Safety

- dashboard_runtime: false
- server: false
- frontend: false
- browser_automation: false
- runtime_wiring: false
- network_api: false
- wallet: false
- trading: false
- autonomous_paper_orders: false
- scoring_probability_ev_edge: false
- market_decisions: false

## Interpretation Warnings

- Paper accounting PnL is fixture/manual accounting only and is not strategy profitability.
- This snapshot does not recommend a side, size, price, market, or trade.
- This snapshot does not contain probability estimates, EV, edge, market scoring, truth inference, live prices, or live fetch results.
- This snapshot reads local artifacts only and does not create executable orders or autonomous paper orders.
