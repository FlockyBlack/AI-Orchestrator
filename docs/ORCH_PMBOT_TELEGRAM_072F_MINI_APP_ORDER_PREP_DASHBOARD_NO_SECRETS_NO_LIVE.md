# ORCH-PMBOT-TELEGRAM-072F Mini App Order Prep Dashboard

Task: `ORCH-PMBOT-TELEGRAM-072F-MINI-APP-ORDER-PREP-DASHBOARD-NO_SECRETS_NO_LIVE`

This task extends the static RU-first Telegram Mini App dashboard with a review-only section titled `🧪 Подготовка первого ордера`.

## What It Shows

- `Рынок`: `BTC`, taken from the committed local 071A public market discovery status artifact.
- `Token ID`: `не выбран`, because the committed local 070B/070A artifacts report `token_id_present=false`.
- `Аккаунт`: `не проверен`, because the committed local 070C read-only account artifact reports missing credential presence and no account probe values.
- `Signer`: `выключен`, because signing remains disabled and was not attempted.
- `Approval`: `не проверен`, because allowance/approval availability is not available in the local read-only artifact.
- `Payload dry-run`: `artifact есть`, because the committed local 070A dry-run payload artifact exists, while remaining non-executable.
- `Live выключен`: `allowed_for_live=false`.

Unavailable values use safe placeholders only. The Mini App does not invent token IDs, account addresses, approval state, balances, orders, trades, PnL, or execution readiness.

## Local Artifact Inputs

The dashboard section is static and reflects committed local artifact snapshots only:

- `pm_bot/trading_core/artifacts/public_market_token_discovery_071a/latest_public_market_token_discovery_status_071a.json`
- `pm_bot/trading_core/artifacts/first_order_market_token_resolver_070b/latest_first_order_market_token_status_070b.json`
- `pm_bot/trading_core/artifacts/live_account_readonly_state_probe_070c/latest_live_account_readonly_state_status_070c.json`
- `pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a/latest_signed_order_payload_dry_run_status_070a.json`

There is no runtime network fetch, no JavaScript, no form, and no secret entry surface. If a local artifact or field is absent in a future snapshot, the UI contract is to show only `не выбран`, `не проверен`, or `выключен`.

## Outputs

Generated under `pm_bot/trading_core/artifacts/telegram_mini_app_order_prep_072f/`:

- `telegram_mini_app_order_prep_072f_result.json`
- `latest_telegram_mini_app_order_prep_status_072f.json`
- `telegram_mini_app_order_prep_ui_snapshot_072f.json`
- `telegram_mini_app_order_prep_safety_snapshot_072f.json`

## Safety Statement

This is a static review-only Mini App dashboard update. It performs no live trading, no order execution, no order management, no signing, no wallet connection, no authenticated endpoint calls, no browser automation, and no secret handling. It adds no production dependency, scheduler, daemon, or background worker.
