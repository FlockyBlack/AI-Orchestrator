# PMBOT Paper Candidate Review Table

Deterministic synthetic candidate table for local operator review only.

| candidate_id | decision | confidence | operator_action | reason |
| --- | --- | --- | --- | --- |
| rq_case_strong_accept | accept | 89 (high) | paper_monitor_no_action | accepted_for_paper_monitoring_only |
| rq_case_low_confidence_watchlist | watchlist | 76 (medium) | watchlist_no_action | limited_supporting_signals |
| rq_case_correlated_watchlist | watchlist | 67 (medium) | watchlist_no_action | correlated_exposure |
| rq_case_missing_note_watchlist | watchlist | 66 (medium) | watchlist_no_action | missing_research_notes |
| rq_case_high_confidence_high_risk | watchlist | 46 (low) | watchlist_no_action | concentration_risk, correlated_exposure, high_risk_profile |
| rq_case_paper_only_no_action | no_action | 60 (low) | review_only | paper_only_no_action |
| rq_case_wide_spread_caution | reject | 57 (reject) | reject_no_action | wide_spread |
| rq_case_low_liquidity_reject | reject | 56 (reject) | reject_no_action | low_liquidity |
| rq_case_stale_data_warning | reject | 55 (reject) | reject_no_action | stale_data |
| rq_case_conflicting_signals_reject | reject | 54 (reject) | reject_no_action | conflicting_signals |
| rq_case_weak_edge_reject | reject | 54 (reject) | reject_no_action | insufficient_edge |
| rq_case_resolved_market_exclusion | exclude | 0 (reject) | reject_no_action | insufficient_edge, low_liquidity, resolved_or_closed_market, stale_data |

- This review table is for paper research and operator review only. No buy, sell, trade, submit_order, execute, live_action, or real_position behavior exists.
