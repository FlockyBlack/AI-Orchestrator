# PM Bot Stage Summary V51

## Scope

PMBOT-RESEARCH-001 added deterministic offline/local single-market research dossier generation for manually selected Polymarket markets.

## Result

- Added `pm_bot/research/single_market_research_packet.v1.json` as the default manual packet fixture.
- Added `pm_bot/research/run_single_market_research_dossier.py`.
- The command `python pm_bot\research\run_single_market_research_dossier.py` emits JSON by default.
- `--markdown` emits a deterministic Markdown dossier.
- `--packet <path>` allows a caller to point at another local packet file.
- The dossier includes market metadata, implied Yes probability, Yes evidence, No evidence, uncertainty factors, reliability notes, missing information, probability range, edge estimate, decision, reason codes, human review note, and safety flags.
- Conservative gates block paper-candidate labels when resolution criteria are missing, sources are weak, evidence is one-sided, or the probability range overlaps the market price.
- Added locked expected JSON and Markdown outputs.
- Added tests for deterministic output, missing resolution criteria, weak sources, overlapping probability range, strong-evidence candidate labeling without orders, existing paper commands, safety flags, no network/wallet/order behavior, and standard-library imports.

## Research Summary

- Market ID: `pm_fixture_single_market_001`
- Sources: 5
- Yes evidence: 3
- No evidence: 1
- Decision: `paper_candidate`
- Paper orders created: 0
- Workspace state written: false

## Safety

- Offline local packet reads only.
- Paper mode only.
- No live web fetching.
- No network or API calls.
- No credentials, wallet, private key, signing, real order, or live trading path.
- No dispatcher, runtime wiring, prompt automation, broad refactor, paper order creation, or workspace state writing.

## Verification

- `python -m pytest pm_bot\research\tests\test_run_single_market_research_dossier.py -q`
- `python -m pytest pm_bot\scoring\tests pm_bot\paper\tests pm_bot\research\tests -q`
- `python pm_bot\research\run_single_market_research_dossier.py`
- `python pm_bot\research\run_single_market_research_dossier.py --markdown`
- `python pm_bot\paper\run_manual_paper_operator_cycle.py`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py`

All verification checks passed.
