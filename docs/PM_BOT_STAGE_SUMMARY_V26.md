# PM Bot Stage Summary V26

Status: `lifecycle_regression_gates_ready_for_review`

`PMBOT-BRAIN-014-LIFECYCLE-REGRESSION-GATES` adds deterministic offline regression gates for crypto numeric paper lifecycle replay.

Run JSON:

```powershell
python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py
```

Run Markdown:

```powershell
python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py --markdown
```

## Gates

- aggregate outcomes remain locked
- bad entries remain zero
- settled-no paper fill guard remains active
- no-action and rejected scenarios do not create paper orders
- winning scenarios still produce expected paper fills
- locked safety flags remain unchanged

## Locked Replay Summary

- scenarios: 7
- filled orders: 3
- wins: 2
- losses: 0
- bad entries: 0
- rejected bad cases: 1
- total paper PnL: 179.31

## Gate Summary

- gates checked: 6
- gates passed: 6
- gates failed: 0
- safety flags locked: true
- bad entries locked zero: true
- settled-no fill guard locked: true

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
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py --markdown`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_replay.py`

## Next Step

Add an offline paper lifecycle audit report that explains why each regression gate passed or failed for operator review.
