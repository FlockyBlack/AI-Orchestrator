# PMBOT PAPER-018 Accounting Batch Audit

- Task ID: `PMBOT-PAPER-018-MULTI-RECORD-PAPER-ACCOUNTING-BATCH-AUDIT`
- Audit status: `batch_audit_passed`
- Records audited: `3`
- Market IDs: `824952, paper-batch-market-open-003, paper-batch-market-settled-loss-002`
- Paper orders created: `0`
- Autonomous actions created: `0`
- Next safe action: `ready_for_integration_review`

## Accounting Totals

| Metric | Value |
| --- | ---: |
| `paper_accounting_total_records` | `3` |
| `paper_accounting_settled_count` | `2` |
| `paper_accounting_open_count` | `1` |
| `paper_accounting_win_count` | `1` |
| `paper_accounting_loss_count` | `1` |
| `paper_accounting_flat_count` | `0` |
| `paper_accounting_total_cost_basis` | `16.00` |
| `paper_accounting_total_settlement_value` | `10.00` |
| `paper_accounting_cumulative_pnl` | `-1.00` |
| `paper_accounting_average_pnl` | `-0.50` |
| `paper_accounting_gross_profit` | `6.00` |
| `paper_accounting_gross_loss` | `-7.00` |
| `paper_accounting_max_gain` | `6.00` |
| `paper_accounting_max_loss` | `-7.00` |

## Records

| Record | Market | Status | PnL | Source |
| --- | --- | --- | ---: | --- |
| `paper-accounting-batch-record-001` | `824952` | `paper_position_settled` | `6.00` | `existing_paper_017_record` |
| `paper-accounting-batch-record-002` | `paper-batch-market-settled-loss-002` | `paper_position_settled` | `-7.00` | `synthetic_paper_accounting_batch_fixture` |
| `paper-accounting-batch-record-003` | `paper-batch-market-open-003` | `paper_position_open` | `0.00` | `synthetic_paper_accounting_batch_fixture` |

## Checks

| Check | Status | Summary |
| --- | --- | --- |
| `source_artifacts_loaded` | `pass` | Required local paper accounting artifacts were loaded. |
| `source_artifacts_deterministic` | `pass` | Source paper accounting artifacts declare deterministic output. |
| `paper_017_reconciliation_anchor` | `pass` | Existing PAPER-017 reconciliation audit is present and passed before batch audit expansion. |
| `record_count_consistency` | `pass` | Batch accounting record counts match the deterministic multi-record audit scope. |
| `existing_record_anchor_consistency` | `pass` | The first batch record remains anchored to the existing local PAPER-017 accounting record. |
| `market_id_consistency` | `pass` | Each batch record keeps the same market_id across fill, settlement, accounting, ledger, and portfolio fields. |
| `fill_settlement_accounting_linkage` | `pass` | Fill, settlement, accounting, ledger, and portfolio identifiers link within each batch record. |
| `open_settled_status_consistency` | `pass` | Open and settled records carry status-compatible settlement and ledger fields. |
| `per_record_pnl_consistency` | `pass` | Each batch record PnL reconciles from local paper fill and settlement values. |
| `pnl_aggregation_consistency` | `pass` | Declared batch accounting totals match deterministic aggregation across audited records. |
| `artifact_pointer_consistency` | `pass` | Batch source pointers and record source references point to the expected local paper artifacts. |
| `safety_flag_consistency` | `pass` | Batch records and source artifact counts remain paper-only, inert, local, and non-executable. |
| `no_scoring_probability_ev_edge_or_market_decision_fields` | `pass` | Audited batch and active source artifacts contain no scoring, probability, EV, edge, recommendation, or market-decision fields. |

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
