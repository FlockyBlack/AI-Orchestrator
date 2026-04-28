# PMBOT Market Shock Report

Deterministic hostile market shock sweep for synthetic PMBOT candidates.

- Total scenarios: 8
- Passed scenarios: 8
- Rejection reasons: {"low_liquidity": 1, "resolved_market": 1, "stale_data": 1, "wide_spread": 1}
- Warning reasons: {"category_exposure_spike": 1, "confidence_downgrade": 1, "correlation_conflict": 1, "outlier_price_move": 1}
- Summary: Shock scenarios stress paper-only decision logic and never produce live execution.

## Scenario Results
- shock_liquidity_collapse: expected reject, actual reject, flags low_liquidity
- shock_spread_explosion: expected reject, actual reject, flags wide_spread
- shock_data_staleness_spike: expected reject, actual reject, flags stale_data
- shock_price_gap: expected watchlist, actual watchlist, flags outlier_price_move
- shock_resolved_status_flip: expected exclude, actual exclude, flags resolved_market
- shock_confidence_downgrade: expected watchlist, actual watchlist, flags confidence_downgrade
- shock_category_exposure_spike: expected watchlist, actual watchlist, flags category_exposure_spike
- shock_correlation_cluster_warning: expected watchlist, actual watchlist, flags correlation_conflict
