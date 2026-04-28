# PM Bot Stage Summary V54

Task: PMBOT-RESEARCH-004-RESEARCH-SHORTLIST-CALIBRATION

Status: passed

## Summary

Added a deterministic, offline operator shortlist layer to `pm_bot\research\run_market_research_candidate_queue.py`.

The existing broad research queue behavior is preserved:

- markets_seen: 500
- candidates_ranked: 148
- high_priority_count: 31
- medium_priority_count: 50
- low_priority_count: 67
- rejected_count: 352

The new operator shortlist defaults to 10 markets and can be changed with `--shortlist-n`.

## Shortlist Calibration

Per ranked candidate, the runner now exposes:

- `operator_shortlist`
- `shortlist_rank`
- `shortlist_score`
- `shortlist_reason_codes`
- `why_selected_for_research`
- `why_not_bet_yet`

The shortlist scoring prefers clear yes/no markets with strong resolution criteria, sufficient liquidity, near or medium deadlines, likely official/news sources, non-meme structure, and packet types already supported by the local research dossier path.

The shortlist downranks or excludes:

- long-horizon political/election markets without a near-term catalyst
- sports futures, especially long-horizon sports futures
- extreme prices unless near-term and verifiable
- low-liquidity markets
- unsupported or unclear packet types

Default top shortlist examples:

1. `540844` - Will bitcoin hit $1m before GTA VI?
2. `540816` - Russia-Ukraine Ceasefire before GTA VI?
3. `540843` - Will China invades Taiwan before GTA VI?
4. `562186` - Will Ken Paxton win the 2026 Texas Republican Primary?
5. `562187` - Will John Cornyn win the 2026 Texas Republican Primary?

## Checks

- `python -m pytest pm_bot\scoring\tests pm_bot\paper\tests pm_bot\research\tests -q` - passed, 313 passed and 3 subtests passed
- `python pm_bot\research\run_market_research_candidate_queue.py` - passed
- `python pm_bot\research\run_market_research_candidate_queue.py --markdown` - passed
- `python pm_bot\research\run_market_research_candidate_queue.py --top-n 20` - passed
- `python pm_bot\research\run_market_research_candidate_queue.py --shortlist-n 5` - passed
- `python pm_bot\research\run_single_market_research_dossier.py` - passed
- `python pm_bot\research\run_research_dossier_scenarios.py` - passed
- `python pm_bot\paper\run_manual_paper_operator_cycle.py` - passed
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py` - passed

## Safety

No live fetching, network/API calls, research packet creation, paper order planning connection, state writes, credentials, wallet access, real orders, trading, runtime wiring, dispatcher changes, or prompt automation were added.
