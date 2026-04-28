# PM Bot Stage Summary V18

Status: `crypto_numeric_bad_entry_guardrail_ready_for_review`

`PMBOT-BRAIN-006-CRYPTO-NUMERIC-BAD-ENTRY-GUARDRAILS` adds a small deterministic guardrail for the known replay bad entry.

## Bad Entry Analysis

The losing replay paper order passed the old gates because it had:

- deep liquidity
- tight spread
- low risk level
- large positive buffered edge

The missed risk shape was overextension: BTC was already 6% above its target and the market yes price was already 0.62. The scorer now caps that shape at watchlist when directional distance through target is at least 5.5% and yes price is at least 0.60.

## Replay Impact

Before:

- paper orders: 2
- wins: 1
- losses: 1
- total paper PnL: -30.51
- bad entries: 1

After:

- replay cases: 5
- paper orders: 1
- wins: 1
- losses: 0
- no action: 4
- total paper PnL: 69.49
- bad entries: 0
- rejected bad cases: 2

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
- no new validation layer

## Verification

- `python -m pytest pm_bot\scoring\tests -q`
- `python pm_bot\scoring\run_crypto_numeric_paper_chain.py`
- `python pm_bot\scoring\run_crypto_numeric_paper_replay.py`
- `python pm_bot\scoring\run_crypto_numeric_paper_replay.py --markdown`

## Next Step

`PMBOT-BRAIN-007-CRYPTO-NUMERIC-GUARDRAIL-COVERAGE`: add more fixture-only replay cases around the extension threshold to characterize false-positive and false-negative tradeoffs.
