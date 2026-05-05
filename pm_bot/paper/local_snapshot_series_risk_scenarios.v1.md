# PMBOT Local Snapshot Series Portfolio Risk Scenarios

Deterministic offline replay of local paper portfolio risk-limit scenarios.

## Summary

- Scenario count: 7
- Paper orders created: 7
- Duplicate orders blocked: 2
- Risk-limit orders blocked: 6
- Realized paper PnL: 100.00
- Bad entries: 0
- Safety flags locked: true

## Risk-Limit Reasons

| reason_code | count |
| --- | --- |
| max_asset_paper_exposure_exceeded | 1 |
| max_open_positions_exceeded | 1 |
| max_orders_per_snapshot_exceeded | 2 |
| max_total_paper_exposure_exceeded | 3 |

## Scenarios

| scenario_id | orders | duplicates | risk_blocks | realized_pnl | bad_entries | reason_counts |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_valid_order_allowed | 1 | 0 | 0 | 100.00 | 0 |  |
| duplicate_market_side_blocked | 1 | 1 | 0 | 0.00 | 0 |  |
| total_exposure_breach_blocked | 1 | 0 | 1 | 0.00 | 0 | max_total_paper_exposure_exceeded=1 |
| asset_exposure_breach_blocked | 1 | 0 | 1 | 0.00 | 0 | max_asset_paper_exposure_exceeded=1 |
| max_orders_per_snapshot_breach_blocked | 1 | 0 | 1 | 0.00 | 0 | max_orders_per_snapshot_exceeded=1 |
| max_open_positions_breach_blocked | 1 | 0 | 1 | 0.00 | 0 | max_open_positions_exceeded=1 |
| mixed_allowed_and_blocked_orders | 1 | 1 | 2 | 0.00 | 0 | max_orders_per_snapshot_exceeded=1, max_total_paper_exposure_exceeded=2 |

## Portfolio Events

| scenario_id | event_type | timestamp | market_id | side | reason |
| --- | --- | --- | --- | --- | --- |
| baseline_valid_order_allowed | paper_order_created | 2026-06-01T12:00:00Z | baseline_btc_above_90000 | above | Paper candidate filled from local series fixture observed_yes_price. |
| baseline_valid_order_allowed | paper_position_settled | 2026-06-30T23:59:00Z | baseline_btc_above_90000 | above |  |
| duplicate_market_side_blocked | paper_order_created | 2026-06-01T12:00:00Z | duplicate_btc_above_90000 | above | Paper candidate filled from local series fixture observed_yes_price. |
| duplicate_market_side_blocked | duplicate_paper_order_blocked | 2026-06-02T12:00:00Z | duplicate_btc_above_90000 | above | Paper position already exists for this market and side. |
| total_exposure_breach_blocked | paper_order_created | 2026-06-01T12:00:00Z | total_btc_above_90000 | above | Paper candidate filled from local series fixture observed_yes_price. |
| total_exposure_breach_blocked | risk_limit_paper_order_blocked | 2026-06-02T12:00:00Z | total_eth_below_3000 | below | Paper order would exceed max_total_paper_exposure. |
| asset_exposure_breach_blocked | paper_order_created | 2026-06-01T12:00:00Z | asset_btc_above_90000 | above | Paper candidate filled from local series fixture observed_yes_price. |
| asset_exposure_breach_blocked | risk_limit_paper_order_blocked | 2026-06-02T12:00:00Z | asset_btc_below_85000 | below | Paper order would exceed max_asset_paper_exposure. |
| max_orders_per_snapshot_breach_blocked | paper_order_created | 2026-06-01T12:00:00Z | orders_btc_above_90000 | above | Paper candidate filled from local series fixture observed_yes_price. |
| max_orders_per_snapshot_breach_blocked | risk_limit_paper_order_blocked | 2026-06-01T12:00:00Z | orders_eth_below_3000 | below | Paper order would exceed max_orders_per_snapshot. |
| max_open_positions_breach_blocked | paper_order_created | 2026-06-01T12:00:00Z | open_btc_above_90000 | above | Paper candidate filled from local series fixture observed_yes_price. |
| max_open_positions_breach_blocked | risk_limit_paper_order_blocked | 2026-06-02T12:00:00Z | open_eth_below_3000 | below | Paper order would exceed max_open_positions. |
| mixed_allowed_and_blocked_orders | paper_order_created | 2026-06-01T12:00:00Z | mixed_btc_above_90000 | above | Paper candidate filled from local series fixture observed_yes_price. |
| mixed_allowed_and_blocked_orders | risk_limit_paper_order_blocked | 2026-06-01T12:00:00Z | mixed_eth_below_3000 | below | Paper order would exceed max_total_paper_exposure.; Paper order would exceed max_orders_per_snapshot. |
| mixed_allowed_and_blocked_orders | duplicate_paper_order_blocked | 2026-06-02T12:00:00Z | mixed_btc_above_90000 | above | Paper position already exists for this market and side. |
| mixed_allowed_and_blocked_orders | risk_limit_paper_order_blocked | 2026-06-02T12:00:00Z | mixed_sol_above_200 | above | Paper order would exceed max_total_paper_exposure. |

## Limitations

- Uses local fixture scenario series only; no live fetcher, network, external API, credentials, wallet access, real orders, or live trading is included.
- Scenario entries are deterministic paper plan artifacts replayed through the same local portfolio duplicate, risk-limit, fill, carry-forward, settlement, exposure, and PnL behavior.
- No runtime integration, command-routing changes, prompt automation, broad refactor, or new validation layer is included.

- offline_only=true; paper_only=true; live_fetcher_implemented=false; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false
