# PM Bot Stage Summary V53

## Scope

PMBOT-RESEARCH-003 added deterministic offline/local market research candidate queue generation from saved Polymarket Gamma snapshots.

## Result

- Added `pm_bot/research/run_market_research_candidate_queue.py`.
- The command `python pm_bot\research\run_market_research_candidate_queue.py` emits JSON by default.
- `--markdown` emits a deterministic Markdown candidate queue.
- `--source <path>` allows a caller to point at another saved local Gamma snapshot.
- `--top-n <int>` controls how many ranked candidates are included in output.
- Added locked expected JSON and Markdown outputs for the default 500-market snapshot.
- Added tests for deterministic JSON, deterministic Markdown, `--top-n`, the real 500-market snapshot, sports-future downranking, clear political/diplomatic/legal ranking, low-liquidity and unclear-market penalties, safety flags, forbidden runtime behavior, standard-library imports, and existing research/paper regression commands.

## Candidate Queue Summary

- Markets seen: 500
- Candidates ranked: 148
- High priority count: 31
- Medium priority count: 50
- Low priority count: 67
- Rejected count: 352

Top candidate examples:

- `562186` - Will Ken Paxton win the 2026 Texas Republican Primary? - high - `political_event` - score 0.954
- `562187` - Will John Cornyn win the 2026 Texas Republican Primary? - high - `political_event` - score 0.954
- `540844` - Will bitcoin hit $1m before GTA VI? - high - `crypto_threshold_hit` - score 0.952
- `540816` - Russia-Ukraine Ceasefire before GTA VI? - high - `diplomatic_event` - score 0.936

Decision reason counts:

- `clear_resolution_criteria`: 342
- `clear_yes_no_market`: 500
- `deadline_in_past`: 15
- `extreme_price_downranked`: 401
- `identifiable_official_or_news_sources_likely`: 213
- `limited_resolution_detail`: 158
- `long_horizon_deadline`: 137
- `low_liquidity`: 98
- `market_price_research_value`: 55
- `medium_horizon_deadline`: 267
- `near_term_deadline`: 81
- `research_queue_candidate`: 148
- `research_rejected`: 352
- `sports_future_downranked`: 34
- `sports_long_horizon_downranked`: 94
- `sufficient_liquidity`: 352
- `thin_liquidity`: 50
- `unclear_meme_or_religious_rejected`: 1
- `weak_source_availability`: 1

## Safety

- Offline local snapshot reads only.
- Paper mode only.
- No live web fetching.
- No network or API calls.
- No credentials, wallet access, signing, real order, or live trading path.
- No dispatcher, runtime wiring, prompt automation, paper order creation, workspace state writing, research packet creation, or connection from research output to paper order planning.

## Verification

- `python -m pytest pm_bot\research\tests\test_run_market_research_candidate_queue.py -q` -> 11 passed
- `python -m pytest pm_bot\scoring\tests pm_bot\paper\tests pm_bot\research\tests -q` -> 308 passed, 3 subtests passed
- `python pm_bot\research\run_market_research_candidate_queue.py` -> passed
- `python pm_bot\research\run_market_research_candidate_queue.py --markdown` -> passed
- `python pm_bot\research\run_market_research_candidate_queue.py --top-n 20` -> passed
- `python pm_bot\research\run_single_market_research_dossier.py` -> passed
- `python pm_bot\research\run_research_dossier_scenarios.py` -> passed
- `python pm_bot\paper\run_manual_paper_operator_cycle.py` -> passed
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py` -> passed

All verification checks passed.
