# PM Bot Stage Summary V28

Status: `live_shaped_snapshot_paper_lifecycle_ready_for_review`

`PMBOT-BRAIN-016-LIVE-SHAPED-SNAPSHOT-TO-PAPER-LIFECYCLE` connects the offline live-shaped snapshot adapter into the existing full offline paper lifecycle.

Run JSON:

```powershell
python pm_bot\paper\run_live_shaped_snapshot_paper_lifecycle.py
```

Run Markdown:

```powershell
python pm_bot\paper\run_live_shaped_snapshot_paper_lifecycle.py --markdown
```

## Lifecycle Scope

- reads `pm_bot\scoring\crypto_numeric_live_shaped_snapshot_fixture.v1.json`
- runs the live-shaped snapshot adapter
- passes adapted raw markets into existing intake and normalization
- scores supported markets
- builds the review table
- builds the paper order plan
- runs the paper execution ledger
- emits portfolio/exposure summary
- preserves adapter rejections and raw/intake rejections with reason codes

## Current Fixture Summary

- snapshot markets: 10
- adapted raw markets: 3
- adapter rejections: 7
- normalized supported: 3
- intake rejections: 0
- markets scored: 3
- paper candidates: 1
- watchlist: 1
- rejected after scoring: 1
- paper orders submitted: 1
- paper orders filled: 1
- open positions: 0
- settled positions: 1
- total paper notional: 100.00
- paper PnL: 72.41

## Safety Boundary

- offline-only
- paper-only
- no live fetcher implemented
- no network/API
- no credentials
- no wallet/private keys/signing
- no real orders
- no live trading
- no runtime wiring
- no dispatcher/run_codex
- no prompt automation
- no standalone fetcher contract harness

## Verification

- `python -m pytest pm_bot\scoring\tests pm_bot\paper\tests -q`
- `python pm_bot\paper\run_live_shaped_snapshot_paper_lifecycle.py`
- `python pm_bot\paper\run_live_shaped_snapshot_paper_lifecycle.py --markdown`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py`

## Next Step

Add a narrow regression gate for the live-shaped snapshot-to-paper lifecycle command so future changes lock this new offline demo path.
