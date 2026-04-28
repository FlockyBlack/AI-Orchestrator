# PMBOT PAPER-019 Multi-Market Paper Run Series

- task_id: `PMBOT-PAPER-019-MULTI-MARKET-PAPER-RUN-SERIES`
- series_status: `series_run_passed`
- run_mode: `deterministic_offline_fixture`
- fixture_path: `pm_bot/paper/paper_run_series_fixture.v1.json`
- markets_seen: `5`
- records_seen: `5`
- records_processed: `4`
- paper_orders_created: `0`
- real_orders_created: `0`
- network_calls: `0`
- commands_executed: `0`
- autonomous_decisions: `0`
- next_safe_action: `ready_for_operator_workbench_visibility_review`

## Accounting Summary

| Metric | Value |
| --- | ---: |
| `paper_accounting_average_settled_pnl` | `-0.33` |
| `paper_accounting_cumulative_pnl` | `-1.00` |
| `paper_accounting_flat_count` | `1` |
| `paper_accounting_gross_loss` | `-7.00` |
| `paper_accounting_gross_profit` | `6.00` |
| `paper_accounting_loss_count` | `1` |
| `paper_accounting_max_gain` | `6.00` |
| `paper_accounting_max_loss` | `-7.00` |
| `paper_accounting_open_cost_basis` | `5.00` |
| `paper_accounting_open_count` | `1` |
| `paper_accounting_settled_cost_basis` | `19.00` |
| `paper_accounting_settled_count` | `3` |
| `paper_accounting_total_cost_basis` | `24.00` |
| `paper_accounting_total_records` | `4` |
| `paper_accounting_total_settlement_value` | `18.00` |
| `paper_accounting_win_count` | `1` |

## Portfolio Summary

| Metric | Value |
| --- | ---: |
| `blocked_records_not_in_portfolio` | `1` |
| `open_paper_positions` | `1` |
| `paper_orders_created` | `0` |
| `paper_positions_seen` | `4` |
| `portfolio_summary_status` | `deterministic_fixture_accounting_summary_ready` |
| `real_orders_created` | `0` |
| `realized_paper_pnl` | `-1.00` |
| `settled_paper_positions` | `3` |
| `unrealized_paper_pnl` | `0.00` |

## Records

| Record | Market | Status | Lifecycle | Outcome | Included | PnL |
| --- | --- | --- | --- | --- | --- | ---: |
| `paper-run-series-record-001` | `paper-series-market-settled-win-001` | `accepted_accounting_record` | `settled` | `positive_pnl` | `true` | `6.00` |
| `paper-run-series-record-002` | `paper-series-market-settled-loss-002` | `accepted_accounting_record` | `settled` | `negative_pnl` | `true` | `-7.00` |
| `paper-run-series-record-003` | `paper-series-market-settled-flat-003` | `accepted_accounting_record` | `settled` | `flat_pnl` | `true` | `0.00` |
| `paper-run-series-record-004` | `paper-series-market-open-manual-004` | `manual_review_only` | `open` | `open_unsettled` | `true` | `0.00` |
| `paper-run-series-record-005` | `paper-series-market-blocked-005` | `blocked_fixture_record` | `blocked` | `not_accounted` | `false` | `` |

## Checks

| Check | Status | Details |
| --- | --- | --- |
| `fixture_metadata_safety` | `pass` | `none` |
| `record_shape_and_safety` | `pass` | `none` |
| `multi_market_lifecycle_coverage` | `pass` | `none` |
| `fixture_accounting_consistency` | `pass` | `none` |
| `no_scoring_probability_ev_edge_or_market_decision_fields` | `pass` | `none` |
| `fixture_expected_summary_alignment` | `pass` | `none` |

## Safety

| Flag | Value |
| --- | --- |
| `automation_daemon` | `false` |
| `autonomous_paper_orders` | `false` |
| `command_execution` | `false` |
| `deterministic` | `true` |
| `fixture_only` | `true` |
| `live_trading` | `false` |
| `local_file_reads_only` | `true` |
| `manual_review_only` | `true` |
| `market_decisions` | `false` |
| `network_api` | `false` |
| `offline_only` | `true` |
| `paper_accounting_only` | `true` |
| `paper_only` | `true` |
| `real_orders` | `false` |
| `runtime_wiring` | `false` |
| `scoring_probability_ev_edge` | `false` |
| `trading` | `false` |
| `truth_inference` | `false` |
| `wallet` | `false` |
