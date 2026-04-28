# PM Bot Stage Summary V52

## Scope

PMBOT-RESEARCH-002 added deterministic offline/local scenario coverage for single-market research dossier decision gates.

## Result

- Added `pm_bot/research/research_dossier_scenarios.v1.json` with 10 required local fixtures.
- Added `pm_bot/research/run_research_dossier_scenarios.py`.
- The command `python pm_bot\research\run_research_dossier_scenarios.py` emits JSON by default.
- `--markdown` emits a deterministic Markdown scenario report.
- `--scenarios <path>` allows a caller to point at another local scenario fixture file.
- Added locked expected JSON and Markdown outputs for the default scenario fixture.
- Added tests for deterministic output, fixture contract, aggregate counts, required scenario decisions, zero order/state behavior, stale-source diagnostics, manual-review-note diagnostics, custom local fixture path support, safety flags, forbidden runtime behavior, and standard-library imports.

## Scenario Summary

- Scenario count: 10
- No action count: 4
- Watchlist count: 5
- Paper candidate count: 1
- Paper orders created: 0
- All expected decisions passed: true
- All expected reason codes present: true

Decision reason counts:

- `estimated_range_below_market`: 1
- `missing_resolution_criteria`: 1
- `one_sided_sources`: 1
- `paper_candidate_label_only`: 1
- `positive_edge_range_above_market`: 1
- `probability_range_overlaps_market`: 4
- `weak_sources`: 2

Covered scenarios:

- `missing_resolution_criteria`
- `weak_sources_only`
- `one_sided_low_reliability_sources`
- `conflicting_evidence`
- `stale_sources`
- `probability_range_overlaps_market_price`
- `strong_sources_but_missing_key_info`
- `strong_sources_clear_edge`
- `high_uncertainty_high_market_price`
- `operator_note_requires_manual_review`

## Safety

- Offline local fixture reads only.
- Paper mode only.
- No live web fetching.
- No network or API calls.
- No credentials, wallet access, signing, real order, or live trading path.
- No dispatcher, runtime wiring, prompt automation, paper order creation, workspace state writing, or connection from research output to paper order planning.

## Verification

- `python -m pytest pm_bot\research\tests\test_run_research_dossier_scenarios.py -q` -> 11 passed
- `python -m pytest pm_bot\scoring\tests pm_bot\paper\tests pm_bot\research\tests -q` -> 297 passed, 3 subtests passed
- `python pm_bot\research\run_research_dossier_scenarios.py` -> passed
- `python pm_bot\research\run_research_dossier_scenarios.py --markdown` -> passed
- `python pm_bot\research\run_single_market_research_dossier.py` -> passed
- `python pm_bot\research\run_single_market_research_dossier.py --markdown` -> passed
- `python pm_bot\paper\run_manual_paper_operator_cycle.py` -> passed
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py` -> passed

All verification checks passed.
