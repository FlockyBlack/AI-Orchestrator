# PM Bot Stage Summary V20

Status: `crypto_numeric_market_intake_ready_for_review`

`PMBOT-BRAIN-008-CRYPTO-NUMERIC-MARKET-INTAKE` adds deterministic offline intake for raw fixture Polymarket-style crypto numeric market records.

Run JSON:

```powershell
python pm_bot\scoring\crypto_numeric_market_intake.py pm_bot\scoring\crypto_numeric_raw_market_fixtures.v1.json
```

Run Markdown:

```powershell
python pm_bot\scoring\crypto_numeric_market_intake.py pm_bot\scoring\crypto_numeric_raw_market_fixtures.v1.json --markdown
```

## Intake Scope

- supports BTC/ETH above or below a numeric target by expiry
- extracts target, side, asset, expiry, yes price, liquidity, spread, and fixture signal fields
- emits a normalized scorer fixture
- rejects unsupported or ambiguous records with reason codes

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
- `python pm_bot\scoring\crypto_numeric_market_intake.py pm_bot\scoring\crypto_numeric_raw_market_fixtures.v1.json`
- `python pm_bot\scoring\crypto_numeric_market_intake.py pm_bot\scoring\crypto_numeric_raw_market_fixtures.v1.json --markdown`

## Next Step

`PMBOT-BRAIN-009-CRYPTO-NUMERIC-INTAKE-TO-CHAIN`: connect the normalized intake output to the existing offline scorer/review/plan chain as a local fixture-only command, without runtime wiring.
