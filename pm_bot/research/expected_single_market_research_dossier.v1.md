# Single-Market Research Dossier

- Market ID: pm_fixture_single_market_001
- Title: Will Example State certify the Metro Rail funding package by July 31, 2026?
- Question: Will Example State certify the Metro Rail funding package by July 31, 2026?
- Current date: 2026-04-27
- Yes price: 0.37
- No price: 0.63
- Implied probability from Yes price: 0.37
- Decision: paper_candidate
- Reason codes: ["positive_edge_range_above_market", "paper_candidate_label_only"]
- Paper orders created: 0

## Resolution Criteria

Resolves Yes if Example State publishes an official certification or final approval notice for the Metro Rail funding package on or before 2026-07-31. Draft notices, committee recommendations, or unofficial social posts do not resolve the market.

## Probability And Edge

- Probability estimate range: {"high": 0.6194, "low": 0.4394, "method": "deterministic_source_weighted_fixture_heuristic", "midpoint": 0.5294}
- Edge estimate vs market: {"market_yes_price": 0.37, "midpoint_edge": 0.1594, "range_high_edge": 0.2494, "range_low_edge": 0.0694, "range_overlaps_market": false}

## Evidence Summary

- Sources: 5
- Yes evidence: 3
- No evidence: 1
- Uncertainty factors: 2
- Missing information: []

## Yes Evidence

- src_official_budget_notice: Example State Budget Office funding certification calendar (weight=3.0)
- src_court_docket_no_stay: Example Superior Court docket entry denying emergency stay (weight=3.0)
- src_local_news_committee: Local News: budget committee advances Metro Rail funding package (weight=1.5)

## No Evidence

- src_policy_analysis_risk: Analyst memo: remaining administrative risk for Metro Rail package (weight=1.125)

## Source Reliability

| source_id | type | direction | reliability | weight | hint |
| --- | --- | --- | --- | --- | --- |
| src_official_budget_notice | official_statement | yes | strong | 3.0 | high primary official source |
| src_court_docket_no_stay | court_record | yes | strong | 3.0 | high primary court record |
| src_local_news_committee | news | yes | medium | 1.5 | medium corroborated local reporting |
| src_policy_analysis_risk | analysis | no | medium | 1.125 | medium scenario analysis |
| src_social_advocate | social | uncertainty | weak | 0.3 | low unverified social source |

## Human Review Note

Paper candidate label only: local evidence clears conservative offline checks; no paper order is created.

## Safety

- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false
