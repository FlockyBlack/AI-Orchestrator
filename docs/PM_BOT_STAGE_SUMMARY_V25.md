# PM Bot Stage Summary V25

Status: `lifecycle_bad_entry_guardrail_ready_for_review`

`PMBOT-BRAIN-013-LIFECYCLE-BAD-ENTRY-GUARDRAIL` fixes the remaining bad lifecycle replay entry without adding regression gates.

## Bad Entry Analysis

The bad replay entry was `filled_loss`.

It passed scorer and paper order planning because its market inputs were intentionally identical to legitimate winning BTC above 90000 candidate cases:

- positive buffered edge
- pass liquidity
- pass spread
- low risk

The only distinguishing signal was in execution fixture lifecycle state: the fixture market was already `settled=true` with `settlement_outcome=no`. That makes this a paper execution ledger handling issue, not a scorer or paper-plan issue.

## Guardrail

The paper execution ledger now blocks a paper fill when fixture execution state says the market is already settled no.

Blocked event reason:

```text
Fixture market is already settled no; paper fill blocked.
```

## Before

- scenarios: 7
- filled orders: 4
- wins: 2
- losses: 1
- total paper PnL: 79.31
- bad entries: 1
- rejected bad cases: 1

## After

- scenarios: 7
- filled orders: 3
- not-filled orders: 2
- wins: 2
- losses: 0
- total paper PnL: 179.31
- bad entries: 0
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
- `python pm_bot\paper\run_crypto_numeric_paper_lifecycle.py`

## Next Step

After review approval, add offline lifecycle regression gates to lock required scenario outcomes and safety flags.
