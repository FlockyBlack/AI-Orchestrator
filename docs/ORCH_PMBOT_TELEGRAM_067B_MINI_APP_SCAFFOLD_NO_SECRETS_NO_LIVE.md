# ORCH-PMBOT-TELEGRAM-067B Mini App Scaffold

## Scope

This task adds a static Telegram Mini App scaffold for PMBOT at `pm_bot/telegram_mini_app/`.

The scaffold is RU-first and contains only passive dashboard placeholders:

- Главная
- Подключение
- Баланс
- Сделки
- PnL
- Статус
- Лимиты
- Стоп

## Runtime Wiring

The Telegram runtime continues to use `PMBOT_TELEGRAM_MINI_APP_URL` as the only Mini App URL marker.

- Configured URL: `/panel` attaches a WebApp button labeled `Открыть PMBOT`.
- Missing URL: `/panel` reports `Mini App URL не настроен`.
- The URL value is redacted from runtime payloads and status reports.

## Scaffold Boundary

- no forms
- no inputs
- no browser storage
- no frontend network calls
- no account data reads
- no invented account values
- no live trading controls
- no order submission or cancellation controls
- no signing controls
- no wallet connection controls
- no authenticated trading calls

## Artifacts

- `pm_bot/trading_core/artifacts/telegram_mini_app_067b/telegram_mini_app_067b_result.json`
- `pm_bot/trading_core/artifacts/telegram_mini_app_067b/latest_telegram_mini_app_status_067b.json`
- `pm_bot/trading_core/artifacts/telegram_mini_app_067b/telegram_mini_app_menu_snapshot_067b.json`
- `pm_bot/trading_core/artifacts/telegram_mini_app_067b/telegram_mini_app_safety_snapshot_067b.json`
- `docs/ORCH_PMBOT_TELEGRAM_067B_MINI_APP_SCAFFOLD_NO_SECRETS_NO_LIVE_RESULT.json`

## Validation

The focused test is:

```powershell
python -m pytest pm_bot/tests/test_telegram_mini_app_scaffold_067b.py
```

Full requested validation is recorded in the result JSON and final operator report.
