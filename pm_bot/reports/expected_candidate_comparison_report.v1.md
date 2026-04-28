# PMBOT Candidate Comparison Report

Deterministic comparison of accepted, watchlist, rejected, excluded, and no-action synthetic cases.

- Notice: Synthetic research comparison only. No trading advice and no real order is created.

## Ranked Candidates
- rq_case_strong_accept: accept | confidence 89 (high) | risk 65 | data-quality 95 | flags none
- rq_case_low_confidence_watchlist: watchlist | confidence 76 (medium) | risk 65 | data-quality 85 | flags none
- rq_case_correlated_watchlist: watchlist | confidence 67 (medium) | risk 35 | data-quality 95 | flags correlated_exposure
- rq_case_missing_note_watchlist: watchlist | confidence 66 (medium) | risk 65 | data-quality 40 | flags missing_research_notes
- rq_case_high_confidence_high_risk: watchlist | confidence 46 (low) | risk 35 | data-quality 95 | flags concentration_risk, correlated_exposure, high_risk_profile
- rq_case_paper_only_no_action: no_action | confidence 60 (low) | risk 65 | data-quality 85 | flags paper_only_no_action
- rq_case_wide_spread_caution: reject | confidence 57 (reject) | risk 90 | data-quality 85 | flags wide_spread
- rq_case_low_liquidity_reject: reject | confidence 56 (reject) | risk 90 | data-quality 85 | flags low_liquidity
- rq_case_stale_data_warning: reject | confidence 55 (reject) | risk 65 | data-quality 15 | flags stale_data
- rq_case_conflicting_signals_reject: reject | confidence 54 (reject) | risk 65 | data-quality 80 | flags conflicting_signals
- rq_case_weak_edge_reject: reject | confidence 54 (reject) | risk 90 | data-quality 85 | flags none
- rq_case_resolved_market_exclusion: exclude | confidence 0 (reject) | risk 90 | data-quality 15 | flags low_liquidity, missing_research_notes, stale_data
