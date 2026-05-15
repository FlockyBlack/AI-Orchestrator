# ORCH-PMBOT-TELEGRAM-067E Wallet/Auth Status Dashboard

Task: `ORCH-PMBOT-TELEGRAM-067E-WALLET-AUTH-STATUS-DASHBOARD-NO-LIVE`

This task adds a Telegram operator status surface for local PMBOT connection readiness. The screen is RU-first and uses the title `🔐 Подключение`.

## What It Shows

- `API ключи`: `добавлены` only when redacted L2 API key, secret, and passphrase presence markers are present.
- `Private key`: `добавлен` only when a redacted private-key presence marker exists.
- `Wallet`: a redacted address such as `0x3006...8989` when a safe local artifact provides one, otherwise `missing` or `configured:redacted`.
- `Signature type`: a non-secret type value such as `3` when provided by an artifact, otherwise `missing`.
- `Funder`: a redacted address when available, otherwise `missing` or `configured:redacted`.
- `L2 auth probe`: `not run`, `ok`, `blocked`, or `failed`, based only on latest local 067C artifact presence/status.
- `Open orders` and `Balance/allowance`: `unknown` unless a real local 067C probe artifact supplies a status.

Values are never shown. The dashboard redacts full address-like values and does not serialize raw credential material.

## Telegram Controls

- `Обновить статус`: routes to `/connection_status` and re-renders local status.
- `Запустить read-only проверку`: routes to safe action `run_connection_status_067e`, which runs `python -m pm_bot.operator_runner.telegram_connection_status_dashboard --dry-run`.
- `Открыть PMBOT Mini App`: added only by runtime decoration when `PMBOT_TELEGRAM_MINI_APP_URL` passes URL safety checks.
- `Назад`: routes to the operator home.

The operator-facing callback/module names intentionally use `connection_status` rather than a wallet token, preserving the existing Telegram forbidden-control safety invariant.

## Artifact Inputs

The builder reads only local JSON artifacts:

- `pm_bot/trading_core/artifacts/explicit_live_credentials_readiness_gate_064/redacted_marker_presence_064.json`
- `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/redacted_l2_marker_presence_058.json`
- latest local 067C CLOB L2 auth read-only probe artifacts, if present

It does not read `.env` files, raw credential values, private key files, wallet files, browser profiles, or credential stores.

## Outputs

Generated under `pm_bot/trading_core/artifacts/telegram_wallet_auth_status_067e/`:

- `telegram_wallet_auth_status_067e_result.json`
- `latest_telegram_wallet_auth_status_067e.json`
- `telegram_wallet_auth_status_menu_snapshot_067e.json`
- `telegram_wallet_auth_status_safety_snapshot_067e.json`

## Safety Statement

This is a dashboard/status task only. It does not connect a wallet, sign payloads, submit or cancel orders, enable live mode, call authenticated endpoints, read balances by itself, or create fake balances/PnL/trades.
