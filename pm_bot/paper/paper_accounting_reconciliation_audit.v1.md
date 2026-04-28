# PMBOT PAPER-017 Accounting Reconciliation Audit

- Task ID: `PMBOT-PAPER-017-PAPER-ACCOUNTING-RECONCILIATION-LIFECYCLE-AUDIT`
- Market ID: `824952`
- Audit status: `reconciliation_passed`
- Paper orders created: `0`
- Autonomous actions created: `0`
- Next safe action: `ready_for_integration_review`

## Accounting Summary

| Metric | Value |
| --- | ---: |
| `paper_accounting_total_records` | `1` |
| `settled_count` | `1` |
| `open_count` | `0` |
| `win_count` | `1` |
| `loss_count` | `0` |
| `flat_count` | `0` |
| `cumulative_pnl` | `6.00` |
| `gross_profit` | `6.00` |
| `gross_loss` | `0.00` |
| `average_pnl` | `6.00` |
| `max_gain` | `6.00` |
| `max_loss` | `0.00` |

## Artifacts Checked

| Artifact | Records | Market IDs | Path |
| --- | ---: | --- | --- |
| `manual_paper_intents_accepted` | `1` | `824952` | `pm_bot/paper/manual_paper_intents_accepted.v1.json` |
| `manual_paper_intent_ledger` | `1` | `824952` | `pm_bot/paper/manual_paper_intent_ledger.v1.json` |
| `paper_workbench_preview` | `1` | `824952` | `pm_bot/paper/paper_workbench_preview.v1.json` |
| `paper_fill_source_fixture` | `3` | `000000, 824952` | `pm_bot/paper/paper_fill_source_fixture.v1.json` |
| `paper_fill_sources_accepted` | `1` | `824952` | `pm_bot/paper/paper_fill_sources_accepted.v1.json` |
| `paper_fill_sources_rejected` | `2` | `000000, 824952` | `pm_bot/paper/paper_fill_sources_rejected.v1.json` |
| `paper_fill_events` | `1` | `824952` | `pm_bot/paper/paper_fill_events.v1.json` |
| `paper_settlement_source_fixture` | `3` | `000000, 824952` | `pm_bot/paper/paper_settlement_source_fixture.v1.json` |
| `paper_settlement_sources_accepted` | `1` | `824952` | `pm_bot/paper/paper_settlement_sources_accepted.v1.json` |
| `paper_settlement_sources_rejected` | `2` | `000000, 824952` | `pm_bot/paper/paper_settlement_sources_rejected.v1.json` |
| `paper_accounting_pnl_preview` | `1` | `824952` | `pm_bot/paper/paper_accounting_pnl_preview.v1.json` |
| `paper_accounting_ledger` | `1` | `824952` | `pm_bot/paper/paper_accounting_ledger.v1.json` |
| `paper_portfolio_snapshot` | `1` | `824952` | `pm_bot/paper/paper_portfolio_snapshot.v1.json` |
| `paper_metrics_report` | `1` | `824952` | `pm_bot/paper/paper_metrics_report.v1.json` |

## Checks

| Check | Status | Summary |
| --- | --- | --- |
| `required_artifacts_present` | `pass` | All required local paper artifacts were loaded. |
| `deterministic_flags` | `pass` | All checked artifacts declare deterministic output. |
| `market_id_consistency` | `pass` | Accepted lifecycle artifacts consistently reference market 824952. |
| `manual_intent_ledger_count_consistency` | `pass` | Accepted manual intent count matches inert manual paper ledger entries. |
| `fill_fixture_partition_consistency` | `pass` | Manual fill fixture records partition into accepted and rejected fill source artifacts. |
| `settlement_fixture_partition_consistency` | `pass` | Manual settlement fixture records partition into accepted and rejected settlement source artifacts. |
| `accepted_lifecycle_record_count_consistency` | `pass` | Accepted lifecycle artifacts each carry one reconciled accounting record. |
| `artifact_pointer_consistency` | `pass` | Artifact pointer fields reference the expected local paper artifacts. |
| `fill_settlement_accounting_linkage` | `pass` | Manual intent, fill, settlement, accounting, ledger, and portfolio ids link across artifacts. |
| `closed_open_status_consistency` | `pass` | Closed and open position counts match accounting ledger, portfolio, and metrics artifacts. |
| `pnl_value_consistency` | `pass` | Accounting PnL values reconcile from local manual fill and settlement fixture values. |
| `portfolio_metrics_consistency` | `pass` | Portfolio snapshot and metrics report values match the accounting ledger. |
| `safety_flag_consistency` | `pass` | Accepted lifecycle artifacts remain paper-only, inert, local, and non-executable. |
| `no_scoring_probability_ev_edge_or_recommendation_fields` | `pass` | Accepted lifecycle artifacts contain no scoring, probability, EV, edge, recommendation, or market-decision fields. |

## Safety

| Flag | Value |
| --- | --- |
| `offline_only` | `true` |
| `local_file_reads_only` | `true` |
| `runtime_wiring` | `false` |
| `network_api` | `false` |
| `wallet` | `false` |
| `trading` | `false` |
| `autonomous_paper_orders` | `false` |
| `scoring_probability_ev_edge` | `false` |
| `market_decisions` | `false` |
| `truth_inference` | `false` |
| `recommendations` | `false` |
