# PM Bot Stage Summary V23

Status: `crypto_numeric_paper_lifecycle_ready_for_review`

`PMBOT-BRAIN-011-CRYPTO-NUMERIC-PAPER-LIFECYCLE-CHAIN` connects the full offline crypto numeric paper lifecycle in one deterministic command.

Run JSON:

```powershell
python pm_bot\paper\run_crypto_numeric_paper_lifecycle.py
```

Run Markdown:

```powershell
python pm_bot\paper\run_crypto_numeric_paper_lifecycle.py --markdown
```

## Lifecycle Scope

- reads `pm_bot\scoring\crypto_numeric_raw_market_fixtures.v1.json`
- normalizes supported BTC/ETH numeric markets
- scores normalized markets
- builds the operator review table
- builds the paper order plan
- runs the paper execution ledger with deterministic fixture execution prices
- emits portfolio/exposure summary
- includes rejected raw markets and scoring rejections

## Current Fixture Summary

- raw markets: 11
- normalized supported: 4
- rejected raw markets: 7
- markets scored: 4
- paper candidates: 1
- watchlist: 1
- rejected after scoring: 2
- paper orders submitted: 1
- paper orders filled: 1
- open positions: 0
- settled positions: 1
- total paper notional: 100.00
- total max loss: 100.00
- paper PnL: 72.41

## Safety Boundary

- offline-only
- paper-only
- no network/API
- no credentials
- no wallet/private keys/signing
- no real orders
- no live trading
- no runtime wiring
- no dispatcher/run_codex
- no prompt automation

## Verification

- `python -m pytest pm_bot\paper\tests pm_bot\scoring\tests -q`
- `python pm_bot\paper\run_crypto_numeric_paper_lifecycle.py`
- `python pm_bot\paper\run_crypto_numeric_paper_lifecycle.py --markdown`

## Next Step

Add offline multi-scenario paper lifecycle replay to compare filled, not-filled, open, and settled position outcomes.
