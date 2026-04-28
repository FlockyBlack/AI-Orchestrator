# PM Bot Stage Summary V55

Task: PMBOT-RESEARCH-005-LOWER-RISK-SHORTLIST-TIERING

Status: passed

## Summary

Refined `pm_bot\research\run_market_research_candidate_queue.py` so the broad research queue and lower-risk operator shortlist are now separate tiers.

The runner remains offline/local only and preserves the existing command:

- `python pm_bot\research\run_market_research_candidate_queue.py`

Default real snapshot output:

- markets_seen: 500
- candidates_ranked: 148
- lower_risk_operator_shortlist_count: 10
- researchable_high_uncertainty_count: 106
- watch_only_count: 32
- rejected_count: 352

## Tiering

Per ranked candidate, the runner now emits:

- `research_tier`
- `risk_tier`
- `uncertainty_reason_codes`
- `operator_shortlist`
- `why_selected_for_research`
- `why_not_lower_risk`
- `why_not_bet_yet`

The lower-risk shortlist now excludes high/extreme risk candidates and strongly downranks:

- GTA VI meta-event framing
- war, invasion, and ceasefire geopolitical tail-risk
- broader geopolitical leadership tail-risk
- long-horizon election or primary markets without a near-term catalyst
- primary markets even when a near-term catalyst exists
- ambiguous or event-dependent resolution
- low liquidity and unsupported packet types

The broad queue remains intact: high-uncertainty markets are still ranked for research review, but they are labeled `researchable_high_uncertainty` or `watch_only` instead of `lower_risk_operator_shortlist`.

## Examples

Lower-risk shortlist examples:

1. `569368` - Will Ivan Cepeda Castro win the 2026 Colombian presidential election?
2. `569366` - Will Abelardo de la Espriella  win the 2026 Colombian presidential election?
3. `569343` - Will Ivan Cepeda Castro win the 1st round of the 2026 Colombian presidential election?
4. `563650` - SCOTUS accepts sports event contract case by July 31, 2026?
5. `569373` - Will Paloma Valencia win the 2026 Colombian presidential election?

High-uncertainty examples retained in the broad queue:

1. `540844` - Will bitcoin hit $1m before GTA VI?
2. `540816` - Russia-Ukraine Ceasefire before GTA VI?
3. `540843` - Will China invades Taiwan before GTA VI?
4. `540820` - Trump out as President before GTA VI?
5. `567688` - Netanyahu out by end of 2026?

## Checks

- `python -m pytest pm_bot\scoring\tests pm_bot\paper\tests pm_bot\research\tests -q` - passed, 318 passed and 3 subtests passed
- `python pm_bot\research\run_market_research_candidate_queue.py` - passed
- `python pm_bot\research\run_market_research_candidate_queue.py --markdown` - passed
- `python pm_bot\research\run_market_research_candidate_queue.py --top-n 20` - passed
- `python pm_bot\research\run_market_research_candidate_queue.py --shortlist-n 5` - passed
- `python pm_bot\research\run_single_market_research_dossier.py` - passed
- `python pm_bot\research\run_research_dossier_scenarios.py` - passed
- `python pm_bot\paper\run_manual_paper_operator_cycle.py` - passed
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py` - passed

## Safety

No live fetching, network/API calls, research packet creation, paper order planning connection, state writes, credentials, wallet access, real orders, trading, runtime wiring, dispatcher changes, prompt automation, broad refactor, or production dependency was added.
