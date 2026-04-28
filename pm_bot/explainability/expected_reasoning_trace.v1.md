# PMBOT Reasoning Trace

Deterministic reasoning traces for fixture-only PMBOT research cases. No network, no wallet, no orders, and no runtime wiring.

## rq_case_strong_accept
- Market: pm_fixture_2026_us_growth_soft_landing
- Decision: accept
- Confidence: high (89)
- Risk flags: none
- Data-quality flags: none
- Safety: No live action, no wallet usage, no order placement, and no runtime wiring.

## rq_case_weak_edge_reject
- Market: pm_fixture_2026_cabinet_exit
- Decision: reject
- Confidence: reject (54)
- Risk flags: none
- Data-quality flags: none
- Safety: No live action, no wallet usage, no order placement, and no runtime wiring.

## rq_case_low_liquidity_reject
- Market: pm_fixture_2026_championship_upset
- Decision: reject
- Confidence: reject (56)
- Risk flags: liquidity is below the deterministic floor
- Data-quality flags: none
- Safety: No live action, no wallet usage, no order placement, and no runtime wiring.

## rq_case_wide_spread_caution
- Market: pm_fixture_2026_cabinet_exit
- Decision: reject
- Confidence: reject (57)
- Risk flags: spread assumptions are too wide for a clean paper entry
- Data-quality flags: none
- Safety: No live action, no wallet usage, no order placement, and no runtime wiring.

## rq_case_stale_data_warning
- Market: pm_fixture_2026_ai_regulation_vote
- Decision: reject
- Confidence: reject (55)
- Risk flags: none
- Data-quality flags: fixture timestamp is stale for deterministic review
- Safety: No live action, no wallet usage, no order placement, and no runtime wiring.

## rq_case_resolved_market_exclusion
- Market: pm_fixture_2026_hurricane_season_closed
- Decision: exclude
- Confidence: reject (0)
- Risk flags: liquidity is below the deterministic floor
- Data-quality flags: fixture timestamp is stale for deterministic review, research note is missing, some case fields are incomplete
- Safety: No live action, no wallet usage, no order placement, and no runtime wiring.

## rq_case_correlated_watchlist
- Market: pm_fixture_2026_cpi_below_target
- Decision: watchlist
- Confidence: medium (67)
- Risk flags: correlated exposure is already elevated
- Data-quality flags: none
- Safety: No live action, no wallet usage, no order placement, and no runtime wiring.

## rq_case_missing_note_watchlist
- Market: pm_fixture_2026_ceasefire_window
- Decision: watchlist
- Confidence: medium (66)
- Risk flags: none
- Data-quality flags: research note is missing, some case fields are incomplete
- Safety: No live action, no wallet usage, no order placement, and no runtime wiring.

## rq_case_conflicting_signals_reject
- Market: pm_fixture_2026_ai_regulation_vote
- Decision: reject
- Confidence: reject (54)
- Risk flags: none
- Data-quality flags: none
- Safety: No live action, no wallet usage, no order placement, and no runtime wiring.

## rq_case_high_confidence_high_risk
- Market: pm_fixture_2026_rate_cut_december
- Decision: watchlist
- Confidence: low (46)
- Risk flags: correlated exposure is already elevated, concentration risk is elevated, overall risk profile is high despite signal strength
- Data-quality flags: none
- Safety: No live action, no wallet usage, no order placement, and no runtime wiring.

## rq_case_low_confidence_watchlist
- Market: pm_fixture_2026_ceasefire_window
- Decision: watchlist
- Confidence: medium (76)
- Risk flags: none
- Data-quality flags: none
- Safety: No live action, no wallet usage, no order placement, and no runtime wiring.

## rq_case_paper_only_no_action
- Market: pm_fixture_2026_ceasefire_window
- Decision: no_action
- Confidence: low (60)
- Risk flags: none
- Data-quality flags: none
- Safety: No live action, no wallet usage, no order placement, and no runtime wiring.
