# PMBOT Watchlist Policy Report

Deterministic encoding of the PMBOT-BATCH-005 warning policy.

- Watchlist is no-action: true
- Watchlist requires human review: true
- Watchlist can execute: false
- Future live mode requires separate approval: true

## Covered Cases
- duplicate_snapshot: replay=replay_adversarial_false_positive, replay_duplicate_snapshot | shock=none | decisions=watchlist_no_action, reject_no_action
- outlier_price_move: replay=replay_adversarial_false_positive, replay_outlier_price_move | shock=shock_price_gap | decisions=watchlist_no_action, reject_no_action
- correlation_conflict: replay=replay_adversarial_false_positive, replay_correlated_opposite_markets | shock=shock_correlation_cluster_warning | decisions=watchlist_no_action, reject_no_action

- Critical rule: Watchlist status is review-only and no-action. It cannot become an accepted, live, order, trade, or execution candidate without separate future approval.
