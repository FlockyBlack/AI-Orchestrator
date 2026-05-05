# Crypto Threshold-Hit Policy Scenarios

- Scenario fixture: pm_bot\paper\threshold_hit_policy_scenarios.v1.json
- Reference context: pm_bot\paper\threshold_hit_reference_context.v1.json
- Decision policy: pm_bot\paper\threshold_hit_decision_policy.v1.json
- Decision policy version: threshold_hit_decision_policy.v1
- As of date: 2026-04-27
- Scenario count: 12
- Reviewed candidates: 11
- No action: 1
- Watchlist: 2
- Policy blocked: 8
- Paper candidates: 0
- Paper orders created: 0
- Policy reason counts: {"before_event_requires_event_model": 1, "deadline_not_future": 1, "deadline_too_near": 1, "liquidity_below_conservative_minimum": 1, "missing_deadline": 1, "missing_liquidity": 1, "missing_reference_price": 1, "missing_yes_price": 1, "paper_candidates_disabled_by_policy": 11, "target_distance_above_watchlist_limit": 1, "target_distance_unavailable": 1, "yes_price_above_conservative_limit": 1}
- All expected decisions passed: true
- All expected results passed: true

## Scenarios

| scenario_id | question | expected | actual | passed_policy_checks | failed_policy_checks | reason_codes | result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| btc_by_date_policy_disabled | Will BTC hit $150k by June 30, 2026? | watchlist | watchlist | ["reference_price_present", "deadline_present", "min_days_to_deadline_for_review", "min_liquidity_for_review", "max_yes_price_for_watchlist", "max_distance_to_target_pct_for_watchlist"] | ["allow_paper_candidates"] | ["paper_candidates_disabled_by_policy"] | pass |
| btc_yes_price_above_limit | Will BTC hit $150k by June 30, 2026? | policy_blocked | policy_blocked | ["reference_price_present", "deadline_present", "min_days_to_deadline_for_review", "min_liquidity_for_review", "max_distance_to_target_pct_for_watchlist"] | ["max_yes_price_for_watchlist", "allow_paper_candidates"] | ["paper_candidates_disabled_by_policy", "yes_price_above_conservative_limit"] | pass |
| btc_distance_above_watchlist_limit | Will BTC hit $200k by June 30, 2026? | policy_blocked | policy_blocked | ["reference_price_present", "deadline_present", "min_days_to_deadline_for_review", "min_liquidity_for_review", "max_yes_price_for_watchlist"] | ["max_distance_to_target_pct_for_watchlist", "allow_paper_candidates"] | ["paper_candidates_disabled_by_policy", "target_distance_above_watchlist_limit"] | pass |
| btc_low_liquidity | Will BTC hit $150k by June 30, 2026? | policy_blocked | policy_blocked | ["reference_price_present", "deadline_present", "min_days_to_deadline_for_review", "max_yes_price_for_watchlist", "max_distance_to_target_pct_for_watchlist"] | ["min_liquidity_for_review", "allow_paper_candidates"] | ["liquidity_below_conservative_minimum", "paper_candidates_disabled_by_policy"] | pass |
| btc_deadline_too_near | Will BTC hit $150k by May 1, 2026? | policy_blocked | policy_blocked | ["reference_price_present", "deadline_present", "min_liquidity_for_review", "max_yes_price_for_watchlist", "max_distance_to_target_pct_for_watchlist"] | ["min_days_to_deadline_for_review", "allow_paper_candidates"] | ["deadline_too_near", "paper_candidates_disabled_by_policy"] | pass |
| btc_before_event_missing_model | Will BTC hit $150k before GTA VI? | policy_blocked | policy_blocked | ["reference_price_present", "min_liquidity_for_review", "max_yes_price_for_watchlist", "max_distance_to_target_pct_for_watchlist"] | ["before_event_event_model_present", "allow_paper_candidates"] | ["before_event_requires_event_model", "paper_candidates_disabled_by_policy"] | pass |
| eth_missing_reference_price | Will ETH reach $5,000 by December 31, 2026? | watchlist | watchlist | ["deadline_present", "min_days_to_deadline_for_review", "min_liquidity_for_review", "max_yes_price_for_watchlist"] | ["reference_price_present", "max_distance_to_target_pct_for_watchlist", "allow_paper_candidates"] | ["missing_reference_price", "paper_candidates_disabled_by_policy", "target_distance_unavailable"] | pass |
| btc_missing_yes_price | Will BTC hit $150k by June 30, 2026? | policy_blocked | policy_blocked | ["reference_price_present", "deadline_present", "min_days_to_deadline_for_review", "min_liquidity_for_review", "max_distance_to_target_pct_for_watchlist"] | ["max_yes_price_for_watchlist", "allow_paper_candidates"] | ["missing_yes_price", "paper_candidates_disabled_by_policy"] | pass |
| btc_missing_liquidity | Will BTC hit $150k by June 30, 2026? | policy_blocked | policy_blocked | ["reference_price_present", "deadline_present", "min_days_to_deadline_for_review", "max_yes_price_for_watchlist", "max_distance_to_target_pct_for_watchlist"] | ["min_liquidity_for_review", "allow_paper_candidates"] | ["missing_liquidity", "paper_candidates_disabled_by_policy"] | pass |
| btc_missing_deadline | Will BTC hit $150k by Q3 2026? | no_action | no_action | ["reference_price_present", "min_liquidity_for_review", "max_yes_price_for_watchlist", "max_distance_to_target_pct_for_watchlist"] | ["deadline_present", "allow_paper_candidates"] | ["missing_deadline", "paper_candidates_disabled_by_policy"] | pass |
| btc_deadline_not_future | Will BTC hit $150k by April 1, 2026? | policy_blocked | policy_blocked | ["reference_price_present", "deadline_present", "min_liquidity_for_review", "max_yes_price_for_watchlist", "max_distance_to_target_pct_for_watchlist"] | ["min_days_to_deadline_for_review", "allow_paper_candidates"] | ["deadline_not_future", "paper_candidates_disabled_by_policy"] | pass |
| unsupported_gold_threshold_rejected | Will gold hit $5,000 by December 31, 2026? | triage_rejected | triage_rejected | [] | [] | ["unsupported_asset"] | pass |

## Safety Flags

- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false

## Limitations

- Reads deterministic local JSON fixtures only; no live fetcher, network, external API, credentials, wallet access, orders, or trading are included.
- Scenarios call the existing threshold-hit triage, review, reference-context, and decision-policy logic.
- No paper orders, runtime wiring, dispatcher changes, prompt automation, or workspace state writes are included.
