# PM Bot Stage Summary V27

Status: `live_shaped_crypto_snapshot_adapter_ready_for_review`

`PMBOT-BRAIN-015-LIVE-SHAPED-MARKET-SNAPSHOT-ADAPTER` adds an offline fixture-only adapter from Polymarket-like read-only market snapshots into existing crypto numeric raw market intake records.

Run JSON:

```powershell
python pm_bot\scoring\adapt_live_shaped_crypto_snapshot.py
```

Run Markdown:

```powershell
python pm_bot\scoring\adapt_live_shaped_crypto_snapshot.py --markdown
```

## Adapter Scope

- reads `pm_bot\scoring\crypto_numeric_live_shaped_snapshot_fixture.v1.json`
- emits raw records compatible with `pm_bot\scoring\crypto_numeric_market_intake.py`
- preserves question, market ID, asset candidate, side candidate, target candidate, expiry, yes price, liquidity, spread, current price, momentum, and volatility fixture fields
- rejects malformed snapshots with deterministic reason codes
- verifies adapted raw records can feed the existing intake/scoring/review/paper-plan chain

## Current Fixture Summary

- snapshot markets: 10
- adapted raw markets: 3
- adapter rejections: 7
- intake chain check passed: true
- chain markets scored: 3
- chain paper candidates: 1
- chain watchlist: 1
- chain rejected after scoring: 1

## Rejection Codes

- missing_question
- missing_market_id
- missing_price
- missing_liquidity
- missing_expiry
- unsupported_asset
- ambiguous_side

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

## Verification

- `python -m pytest pm_bot\scoring\tests pm_bot\paper\tests -q`
- `python pm_bot\scoring\adapt_live_shaped_crypto_snapshot.py`
- `python pm_bot\scoring\adapt_live_shaped_crypto_snapshot.py --markdown`
- `python pm_bot\scoring\run_crypto_numeric_intake_to_chain.py`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py`

## Next Step

Add an offline read-only fetcher contract test harness that validates future fetched snapshots against the live-shaped fixture contract without network calls.
