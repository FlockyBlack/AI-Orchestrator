# PMBOT Bad-Signal Rejection Report

Deterministic rejection review for fixture-only PMBOT research cases.

- Rejected cases count: 6
- Rejection reasons grouped: {"conflicting_signals": 1, "insufficient_edge": 2, "low_liquidity": 2, "resolved_or_closed_market": 1, "stale_data": 2, "wide_spread": 1}
- Confirmation: All rejected cases remain paper-only and produce no real order.

## Examples
- rq_case_weak_edge_reject: insufficient_edge; improve via Improve the synthetic edge or downgrade the case to no-action.
- rq_case_low_liquidity_reject: low_liquidity; improve via Use a synthetic case with liquidity above the local floor.
- rq_case_wide_spread_caution: wide_spread; improve via Tighten spread assumptions before promoting the case.
- rq_case_stale_data_warning: stale_data; improve via Refresh the local fixture timestamp before reconsidering the case.
- rq_case_resolved_market_exclusion: insufficient_edge, low_liquidity, resolved_or_closed_market, stale_data; improve via Improve the synthetic edge or downgrade the case to no-action. | Use a synthetic case with liquidity above the local floor. | Exclude resolved or closed markets from forward research. | Refresh the local fixture timestamp before reconsidering the case.
- rq_case_conflicting_signals_reject: conflicting_signals; improve via Resolve the contradiction between synthetic signals.
