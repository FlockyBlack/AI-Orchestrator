# ORCH-PMBOT-TELEGRAM-071E Order Prep Status Screen

Task: `ORCH-PMBOT-TELEGRAM-071E-ORDER-PREP-STATUS-SCREEN-NO-LIVE`

This task adds a Telegram product status screen for first-order preparation. The screen is RU-first and uses the title `🧪 Подготовка первого ордера`.

## What It Shows

- `Рынок`: `найден` when a local discovery/resolver artifact indicates a market candidate or resolved market; otherwise `не найден`.
- `Token ID`: `найден` only when a local token resolver or payload contract artifact indicates a selected token; otherwise `требуется выбор`.
- `Аккаунт`: `не проверен` without a local read-only account artifact, `read-only OK` for a successful local read-only probe artifact, or `ошибка` for a failed artifact.
- `Подпись`: `не выполнялась` unless a local dry-run payload contract artifact indicates the contract is ready.
- `Отправка ордера`: always `выключена`.
- `Live`: always `выключен`.

The screen intentionally shows readiness labels only. It does not show raw token IDs, account addresses, balances, trades, PnL, source payloads, or technical gate/provider labels.

## Telegram Controls

- `Обновить статус`: routes to `/order_prep_status` and re-renders the latest local 071E status summary.
- `Назад`: routes to the operator home.

There is no Telegram run action for this screen. Telegram does not generate source artifacts, sign payloads, submit/cancel orders, connect a wallet, or call authenticated endpoints.

## Artifact Inputs

The builder reads only local JSON artifacts when present:

- `pm_bot/trading_core/artifacts/public_market_token_discovery_071a/latest_public_market_token_discovery_status_071a.json`
- `pm_bot/trading_core/artifacts/public_market_token_discovery_071a/public_market_token_discovery_071a_result.json`
- `pm_bot/trading_core/artifacts/first_order_market_token_resolver_070b/latest_first_order_market_token_status_070b.json`
- `pm_bot/trading_core/artifacts/first_order_market_token_resolver_070b/first_order_market_token_resolver_070b_result.json`
- `pm_bot/trading_core/artifacts/live_account_readonly_state_probe_070c/latest_live_account_readonly_state_status_070c.json`
- `pm_bot/trading_core/artifacts/live_account_readonly_state_probe_070c/live_account_readonly_state_probe_070c_result.json`
- `pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a/latest_signed_order_payload_dry_run_status_070a.json`
- `pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a/signed_order_payload_dry_run_070a_result.json`
- `pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a/signed_order_payload_contract_070a.json`

Missing source artifacts are normal on base branches that do not yet include 070A/070B/070C/071A. Missing inputs produce conservative labels rather than invented readiness.

## Outputs

Generated under `pm_bot/trading_core/artifacts/telegram_order_prep_status_071e/`:

- `telegram_order_prep_status_071e_result.json`
- `latest_telegram_order_prep_status_071e.json`
- `telegram_order_prep_status_menu_snapshot_071e.json`
- `telegram_order_prep_status_safety_snapshot_071e.json`

## Safety Statement

This is a local status screen only. It performs no live trading, no order submit/cancel, no signing, no wallet connection, no authenticated Telegram-side calls, no browser automation, and no fake balances/trades/PnL. Existing same-message menu behavior is left unchanged; 069C is not present on this base branch.
