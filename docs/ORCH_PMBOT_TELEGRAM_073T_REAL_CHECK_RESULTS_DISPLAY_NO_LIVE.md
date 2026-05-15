# ORCH-PMBOT-TELEGRAM-073T Real-Check Results Display No Live

## Scope

This task adds a user-facing connection-check display for Telegram and the static Telegram Mini App. The display reads only local artifacts from the 072C local real-check bundle and, when present, 073A real-check snapshot artifacts.

## Telegram Screen

The main `🔐 Подключение` product button now renders:

- `🔐 Проверка подключения`
- `API ключи: найдены / не найдены`
- `L2 auth: OK / ошибка / не проверено`
- `Аккаунт: OK / ошибка / не проверен`
- `Signer: OK / ошибка / не проверен`
- `Рынок: найден / не найден`
- `Token ID: выбран / требуется выбор`
- `Live: выключен`

Controls are scoped to:

- `🔄 Обновить` -> same-message refresh of the local display
- `🧪 Запустить локальную проверку` -> `python -m pm_bot.operator_runner.local_real_check_bundle --market BTC --strategy tiny-momentum --dry-run`
- `⬅️ Назад` -> home

The local check action is registered as a synchronous safe Telegram action. It is not a background loop, scheduler, daemon, wallet connector, signing path, submit path, or cancel path.

## Mini App

The static Mini App connection card is now `Проверка подключения` and mirrors the same redacted statuses. If no local real-check artifacts are available, the 073T builder emits `Проверка ещё не запускалась`.

The Mini App remains static:

- no forms
- no inputs
- no scripts
- no `fetch`
- no credential display
- no wallet connection
- no live controls

## Artifacts

Generated under `pm_bot/trading_core/artifacts/telegram_real_check_results_073t/`:

- `telegram_real_check_results_073t_result.json`
- `latest_telegram_real_check_results_status_073t.json`
- `telegram_real_check_results_menu_snapshot_073t.json`
- `telegram_real_check_results_mini_app_snapshot_073t.json`
- `telegram_real_check_results_safety_snapshot_073t.json`

## Safety Statement

073T is display-only. It does not enable live trading, order submission, order cancellation, signing, wallet connection, authenticated Telegram/Mini App rendering calls, raw secret output, fake balances, fake trades, fake PnL, browser automation, schedulers, daemons, background workers, or autonomous trading.
