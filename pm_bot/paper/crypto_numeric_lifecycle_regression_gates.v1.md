# PMBOT Crypto Numeric Lifecycle Regression Gates

Deterministic offline regression gates for crypto numeric paper lifecycle replay.

## Gate Summary

- Status: passed
- Gates checked: 6
- Gates passed: 6
- Gates failed: 0
- Safety flags locked: true
- Bad entries locked zero: true
- Settled-no fill guard locked: true

## Locked Replay Summary

- Scenarios: 7
- Filled orders: 3
- Wins: 2
- Losses: 0
- Bad entries: 0
- Rejected bad cases: 1
- Total paper PnL: 179.31

## Gates

| gate_id | passed |
| --- | --- |
| aggregate_outcomes_locked | true |
| bad_entries_locked_zero | true |
| settled_no_fill_guard_locked | true |
| no_action_and_rejected_do_not_order | true |
| winning_scenarios_still_fill | true |
| safety_flags_locked | true |

## Limitations

- Validates deterministic fixture replay output only; no live markets, prices, or APIs are fetched.
- Regression gates lock current offline paper lifecycle outcomes and safety flags.
- No runtime integration, prompt automation, credentials, wallet access, real orders, or live trading is included.

- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false
