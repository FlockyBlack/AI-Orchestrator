# PM Bot Stage Summary V17

Status: `crypto_numeric_paper_replay_ready_for_review`

`PMBOT-BRAIN-005-CRYPTO-NUMERIC-PAPER-REPLAY` adds deterministic offline/paper replay for crypto numeric scorer, review, and paper-plan decisions.

Run JSON:

```powershell
python pm_bot\scoring\run_crypto_numeric_paper_replay.py
```

Run Markdown:

```powershell
python pm_bot\scoring\run_crypto_numeric_paper_replay.py --markdown
```

## Replay Scope

- uses fixture-only replay cases
- runs scorer -> review table -> paper order plan for historical-style snapshots
- computes paper-only win/loss/no-action results and simulated paper PnL
- reports paper orders, wins, losses, no-actions, bad entries, and rejected bad cases

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
- `python pm_bot\scoring\run_crypto_numeric_paper_replay.py`
- `python pm_bot\scoring\run_crypto_numeric_paper_replay.py --markdown`

## Next Step

`PMBOT-BRAIN-006-CRYPTO-NUMERIC-REPLAY-REPORTING`: add aggregate replay reporting only if review needs presentation improvements. Do not add live fetchers, APIs, wallets, real orders, live trading, runtime wiring, prompt automation, or new validation layers.
