# PM Bot Stage Summary V21

Status: `crypto_numeric_intake_to_chain_ready_for_review`

`PMBOT-BRAIN-009-CRYPTO-NUMERIC-INTAKE-TO-CHAIN` connects the offline raw crypto numeric market intake to the existing scorer -> review table -> paper order plan chain.

Run JSON:

```powershell
python pm_bot\scoring\run_crypto_numeric_intake_to_chain.py
```

Run Markdown:

```powershell
python pm_bot\scoring\run_crypto_numeric_intake_to_chain.py --markdown
```

## Pipeline Scope

- reads `pm_bot\scoring\crypto_numeric_raw_market_fixtures.v1.json`
- normalizes supported BTC/ETH numeric above/below markets
- passes normalized supported markets into the scorer
- builds the operator review table
- builds the paper order plan
- includes rejected raw markets with deterministic reason codes and reasons

## Current Fixture Summary

- raw markets: 11
- normalized supported: 4
- rejected raw markets: 7
- markets scored: 4
- paper candidates: 1
- watchlist: 1
- rejected after scoring: 2
- paper limit orders: 1
- total planned paper notional: 100.00
- max loss: 100.00

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

- `python -m pytest pm_bot\scoring\tests -q`
- `python pm_bot\scoring\run_crypto_numeric_intake_to_chain.py`
- `python pm_bot\scoring\run_crypto_numeric_intake_to_chain.py --markdown`

## Next Step

Add a concise offline demo review bundle that points reviewers to the intake-to-chain JSON and Markdown artifacts.
