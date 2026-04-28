# PM Bot Stage Summary V24

Status: `crypto_numeric_lifecycle_replay_ready_for_review`

`PMBOT-BRAIN-012-MULTI-SCENARIO-PAPER-LIFECYCLE-REPLAY` adds deterministic offline replay scenarios for crypto numeric paper lifecycle outcomes.

Run JSON:

```powershell
python pm_bot\paper\run_crypto_numeric_lifecycle_replay.py
```

Run Markdown:

```powershell
python pm_bot\paper\run_crypto_numeric_lifecycle_replay.py --markdown
```

## Replay Scope

- uses `pm_bot\paper\crypto_numeric_lifecycle_replay_cases.v1.json`
- composes intake, scoring, review, paper order plan, and paper execution ledger per scenario
- covers filled win, filled loss, not-filled, open position, settled position, rejected raw market, and no-action outcomes
- emits per-scenario lifecycle status and portfolio/exposure fields
- emits aggregate replay summary

## Current Fixture Summary

- scenarios: 7
- filled orders: 4
- not-filled orders: 1
- open positions: 1
- settled positions: 3
- wins: 2
- losses: 1
- total paper PnL: 79.31
- bad entries: 1
- rejected bad cases: 1

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
- `python pm_bot\paper\run_crypto_numeric_lifecycle_replay.py`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_replay.py --markdown`

## Next Step

Add offline lifecycle regression gates that fail if required replay scenario outcomes or locked safety flags change.
