# ORCH PMBOT Telegram 064T Credentials Readiness Review Panel

## Scope

This task adds a passive Telegram review panel for the 064 explicit live credentials readiness gate.

The panel reads only local 064 artifacts from:

- `pm_bot/trading_core/artifacts/explicit_live_credentials_readiness_gate_064/`

It does not read `.env` files, credential stores, wallet profiles, browser profiles, raw environment values, private keys, mnemonics, API secrets, auth tokens, passphrases, balances, positions, fills, or PnL.

## Telegram Surface

The new Telegram command is:

- `/credentials_readiness_review`

The new view callback is:

- `pmbot:credentials_readiness_review`

The panel shows:

- credentials readiness status
- required marker presence or absence
- redacted marker labels only
- missing marker blockers
- `allowed_for_live=false`
- `resolved_blocker_count=0`
- `credential_values_read=false`
- `raw_values_emitted=false`
- `broad_environment_scan_performed=false`

The panel includes this warning:

```text
Presence-only review cannot validate whether credential values are correct, usable, funded, authorized, or safe. It checks marker names only. Live execution remains blocked.
```

## Labels

English labels:

- Credentials readiness review
- Presence-only
- Values never shown
- Not live-enabled
- Dry-run only

Russian labels:

- Проверка готовности credentials
- Только наличие маркеров
- Значения не показываются
- Live не включён
- Только dry-run

## Safe Dry-Run

The only 064T action exposed by the credentials readiness review panel is the existing dry-run command:

```powershell
python -m pm_bot.operator_runner.explicit_live_credentials_readiness_gate --market BTC --strategy tiny-momentum --dry-run
```

The command remains dry-run only. It refreshes review artifacts only and does not validate credential correctness, call authenticated endpoints, connect wallets, instantiate signers, generate signed payloads, submit orders, cancel orders, or fetch balances, positions, fills, or PnL.

## Generated 064T Artifacts

The implementation writes deterministic Telegram review artifacts to:

- `pm_bot/trading_core/artifacts/telegram_credentials_readiness_review_064t/telegram_credentials_readiness_review_064t_result.json`
- `pm_bot/trading_core/artifacts/telegram_credentials_readiness_review_064t/latest_telegram_credentials_readiness_review_status_064t.json`
- `pm_bot/trading_core/artifacts/telegram_credentials_readiness_review_064t/telegram_credentials_readiness_review_controls_064t.json`
- `pm_bot/trading_core/artifacts/telegram_credentials_readiness_review_064t/telegram_credentials_readiness_review_registry_snapshot_064t.json`

## Safety Statement

This implementation is passive review / dry-run only. It adds no live trading, no order submission, no order cancellation, no signing, no signer instantiation, no signed payload generation, no wallet connection, no authenticated network calls, no broad environment enumeration, no raw credential reads, and no Telegram approve-live/send-order/sign/wallet controls.
