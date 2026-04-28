# Research Dossier Scenario Coverage

- Task ID: PMBOT-RESEARCH-002-RESEARCH-DOSSIER-SCENARIO-COVERAGE
- Scenario count: 10
- No action count: 4
- Watchlist count: 5
- Paper candidate count: 1
- Paper orders created: 0
- All expected decisions passed: true
- All expected reason codes present: true

## Decision Reason Counts

- estimated_range_below_market: 1
- missing_resolution_criteria: 1
- one_sided_sources: 1
- paper_candidate_label_only: 1
- positive_edge_range_above_market: 1
- probability_range_overlaps_market: 4
- weak_sources: 2

## Scenarios

| scenario_id | expected | actual | passed | reason_codes | paper_orders_created |
| --- | --- | --- | --- | --- | --- |
| missing_resolution_criteria | no_action | no_action | true | ["missing_resolution_criteria"] | 0 |
| weak_sources_only | no_action | no_action | true | ["weak_sources"] | 0 |
| one_sided_low_reliability_sources | no_action | no_action | true | ["weak_sources"] | 0 |
| conflicting_evidence | watchlist | watchlist | true | ["probability_range_overlaps_market"] | 0 |
| stale_sources | watchlist | watchlist | true | ["probability_range_overlaps_market"] | 0 |
| probability_range_overlaps_market_price | watchlist | watchlist | true | ["probability_range_overlaps_market"] | 0 |
| strong_sources_but_missing_key_info | watchlist | watchlist | true | ["one_sided_sources"] | 0 |
| strong_sources_clear_edge | paper_candidate | paper_candidate | true | ["positive_edge_range_above_market", "paper_candidate_label_only"] | 0 |
| high_uncertainty_high_market_price | no_action | no_action | true | ["estimated_range_below_market"] | 0 |
| operator_note_requires_manual_review | watchlist | watchlist | true | ["probability_range_overlaps_market"] | 0 |

## Safety

- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false
