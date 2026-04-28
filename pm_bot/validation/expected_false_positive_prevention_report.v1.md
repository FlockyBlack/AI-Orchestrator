# PMBOT False-Positive Prevention Report

Deterministic assessment of whether hostile replay cases are contained before any future live-data work.

- Total adversarial cases: 12
- Cases correctly rejected: 8
- False positives: 0
- High-risk false positives: 0
- Missed warnings: 0
- Strongest rejection reasons: confidence_vs_data_mismatch, conflicting_signals, low_liquidity, stale_data, wide_spread
- Statement: False-positive prevention remains a local paper-only validation layer. No real order path exists.

## Weakest Current Detection Areas
- Duplicate snapshots are downgraded to watchlist rather than hard rejected.
- Outlier price moves still rely on watchlist downgrades instead of exclusion.
- Correlation contradictions are contained but not treated as universal hard rejects.

## Recommended Future Fixture Additions
- Add multi-step replay cases where shocks arrive in different orders.
- Add synthetic cases with repeated stale-to-fresh oscillations.
- Add fixture sets for category exposure interactions across several watchlist markets.
