# PMBOT Adversarial Replay Report

Deterministic replay validation for hostile synthetic PMBOT market cases.

- Total cases: 12
- Passed cases: 12
- Failed cases: 0
- False positives: 0
- Decision counts: {"accept": 0, "exclude": 1, "reject": 7, "watchlist": 4}
- Strongest rejection reasons: confidence_vs_data_mismatch, conflicting_signals, low_liquidity, stale_data
- Summary: Replay runner validates adversarial fixtures only. No network, no API, no wallet, and no real order path.

## Case Results
- replay_stale_edge_trap: expected reject, actual reject, flags stale_data
- replay_liquidity_collapse: expected reject, actual reject, flags low_liquidity
- replay_spread_widening_spike: expected reject, actual reject, flags wide_spread
- replay_conflicting_inputs: expected reject, actual reject, flags conflicting_signals
- replay_correlated_opposite_markets: expected watchlist, actual watchlist, flags correlation_conflict
- replay_resolved_candidate_leak: expected exclude, actual exclude, flags resolved_market
- replay_missing_market_status: expected reject, actual reject, flags missing_market_status
- replay_duplicate_snapshot: expected watchlist, actual watchlist, flags duplicate_snapshot
- replay_outlier_price_move: expected watchlist, actual watchlist, flags outlier_price_move
- replay_overconfident_poor_data: expected reject, actual reject, flags confidence_vs_data_mismatch, confidence_downgrade
- replay_watchlist_escalation_block: expected watchlist, actual watchlist, flags watchlist_only
- replay_adversarial_false_positive: expected reject, actual reject, flags stale_data, low_liquidity, wide_spread, conflicting_signals, confidence_vs_data_mismatch, correlation_conflict, duplicate_snapshot, outlier_price_move, confidence_downgrade, category_exposure_spike
