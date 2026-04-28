# PM Bot Stage Summary V13

Status: `crypto_numeric_market_scorer_ready_for_review`

`PMBOT-BRAIN-001-CRYPTO-NUMERIC-MARKET-SCORER` adds the first deterministic offline/paper PMBOT decision brain for crypto numeric Polymarket-style fixtures.

Run:

```powershell
python pm_bot\scoring\crypto_numeric_market_scorer.py pm_bot\scoring\crypto_numeric_fixture.v1.json
```

## Scoring Scope

- BTC above target by expiry
- ETH below target by expiry
- fixture-only current prices, market yes prices, liquidity, spread, risk level, momentum, and volatility
- deterministic model probability, market probability, raw edge, buffered edge, and decision gates

## Decisions

- `paper_candidate`: positive buffered edge above the candidate floor with passing liquidity, spread, and risk gates
- `watchlist`: positive buffered edge that still needs review due to threshold or watch-level risk
- `reject`: non-positive buffered edge or failed liquidity, spread, or risk gates

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
- `python pm_bot\scoring\crypto_numeric_market_scorer.py pm_bot\scoring\crypto_numeric_fixture.v1.json`

## Next Step

`PMBOT-BRAIN-002-CRYPTO-NUMERIC-REVIEW-TABLE`: add a paper-only operator review table for the crypto numeric scorer outputs, reusing the existing operator/report patterns. Do not add live fetchers, network/API calls, credentials, wallet handling, real orders, live trading, runtime wiring, dispatcher/run_codex integration, or prompt automation.
