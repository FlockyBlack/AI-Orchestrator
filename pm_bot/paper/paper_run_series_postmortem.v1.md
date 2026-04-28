# PMBOT PAPER-020 Paper Run Series Postmortem

- task_id: `PMBOT-PAPER-020-PAPER-RUN-SERIES-POSTMORTEM`
- postmortem_status: `postmortem_completed`
- source_paper_019: `pm_bot/paper/multi_market_paper_run_series.v1.json`
- source_series_status: `series_run_passed`
- next_safe_action: `PMBOT-WORKBENCH-006-SURFACE-PAPER-020-POSTMORTEM or PMBOT-PRODUCT-002-NEXT-MVP-GATE-REVIEW`

## Source Artifacts

| Artifact | Path | Present | Parse |
| --- | --- | --- | --- |
| `dashboard_003_result` | `docs/PMBOT_DASHBOARD_003_RESULT.json` | `true` | `parsed` |
| `paper_019_result` | `docs/PMBOT_PAPER_019_RESULT.json` | `true` | `parsed` |
| `paper_019_multi_market_run_series` | `pm_bot/paper/multi_market_paper_run_series.v1.json` | `true` | `parsed` |
| `paper_019_multi_market_run_series_markdown` | `pm_bot/paper/multi_market_paper_run_series.v1.md` | `true` | `not_applicable` |
| `paper_019_fixture` | `pm_bot/paper/paper_run_series_fixture.v1.json` | `true` | `parsed` |
| `paper_019_exporter` | `pm_bot/paper/run_multi_market_paper_run_series.py` | `true` | `not_applicable` |
| `operator_review_pack_json` | `pm_bot/workbench/operator_review_pack.v1.json` | `true` | `parsed` |
| `operator_review_pack_markdown` | `pm_bot/workbench/operator_review_pack.v1.md` | `true` | `not_applicable` |
| `static_operator_report_summary` | `pm_bot/dashboard/static_operator_report_summary.v1.json` | `true` | `parsed` |
| `static_operator_report_html` | `pm_bot/dashboard/static_operator_report.v1.html` | `true` | `not_applicable` |
| `artifact_health_report` | `pm_bot/quality/artifact_health_report.v1.json` | `true` | `parsed` |

## Operator Summary

- markets_seen: `5`
- records_seen: `5`
- records_processed: `4`
- cumulative_pnl: `-1.00`

## Accounting-Only Warning

PAPER-019 PnL is accounting-only fixture output, not strategy profitability; it is not a recommendation, edge, EV, probability estimate, market score, or market truth evidence.

## Record Statuses

| Status | Count | Operator Meaning |
| --- | ---: | --- |
| `accepted_accounting_record` | `3` | Record was accepted from the local fixture for accounting summary only. |
| `manual_review_only` | `1` | Record remains an open manual-review fixture item; it is inert and does not create orders. |
| `blocked_fixture_record` | `1` | Record was retained as blocked fixture context and excluded from accounting. |

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

## Accepted Records

| Record | Market | Lifecycle | Outcome | Cost | Settlement | PnL |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `paper-run-series-record-001` | `paper-series-market-settled-win-001` | `settled` | `positive_pnl` | `4.00` | `10.00` | `6.00` |
| `paper-run-series-record-002` | `paper-series-market-settled-loss-002` | `settled` | `negative_pnl` | `7.00` | `0.00` | `-7.00` |
| `paper-run-series-record-003` | `paper-series-market-settled-flat-003` | `settled` | `flat_pnl` | `8.00` | `8.00` | `0.00` |

## Blocked And Manual Review

Manual-review-only records remain inert local fixture records until a future fixture explicitly settles them.
Blocked fixture records are retained for operator context and excluded from accounting totals.

| Record | Status | Lifecycle | Included | Reason |
| --- | --- | --- | --- | --- |
| `paper-run-series-record-004` | `manual_review_only` | `open` | `true` | `manual_review_open_fixture` |
| `paper-run-series-record-005` | `blocked_fixture_record` | `blocked` | `false` | `fixture_record_marked_blocked, operator_manual_accounting_values_not_accepted` |

## Fixture Limitations

- The series has five local fixture records and is not statistically representative.
- All accounting values are explicit fixture values; no live settlement truth is inferred.
- Only one open manual-review record and one blocked record are represented.
- No fees, liquidity, orderbook state, slippage, fill uncertainty, or timing variance are modeled.
- The fixture does not validate market discovery, live data handling, wallet access, or execution behavior.

## Safety Summary

| Counter | Value |
| --- | ---: |
| `autonomous_decisions` | `0` |
| `autonomous_paper_orders` | `0` |
| `commands_executed` | `0` |
| `network_calls` | `0` |
| `real_orders_created` | `0` |

| Flag | Value |
| --- | --- |
| `automation_daemon` | `false` |
| `autonomous_paper_orders` | `false` |
| `command_execution` | `false` |
| `dashboard_server` | `false` |
| `deterministic` | `true` |
| `fixture_only` | `true` |
| `live_trading` | `false` |
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

## Next Safe Actions

- Add more settled fixture records covering additional cost and settlement combinations.
- Add more open manual-review fixture records that remain inert until explicit fixture settlement values exist.
- Add blocked fixture variants for malformed accounting values and unsafe lineage flags.
- Add boundary accounting examples for zero cost, zero settlement, and unusually large fixture values.
- Next task: `PMBOT-WORKBENCH-006-SURFACE-PAPER-020-POSTMORTEM or PMBOT-PRODUCT-002-NEXT-MVP-GATE-REVIEW`
