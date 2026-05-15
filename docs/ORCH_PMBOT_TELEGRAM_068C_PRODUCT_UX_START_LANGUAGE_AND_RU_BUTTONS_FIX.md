# ORCH PMBOT Telegram 068C Product UX Start Language and RU Buttons Fix

## Scope

068C fixes the Telegram PMBOT entry UX so `/start` opens with a language picker before showing any product menu. It keeps the bot review/status/dry-run only and does not add live trading, signing, wallet connection, authenticated trading calls, order submission, or order cancellation.

## Start Screen

`/start` shows only the language choice:

- 🇷🇺 Русский
- 🇬🇧 English

Selecting `🇷🇺 Русский` stores the local operator language as `ru` in `telegram_operator_control_state.operator_language` when runtime state persistence is configured, or in deterministic adapter memory when no artifact directory is configured. Selecting `🇬🇧 English` stores `en` the same way.

## RU Main Menu

The RU product menu is:

- 🔐 Подключение
- 💰 Баланс
- 📊 Сделки
- 📈 PnL
- 🤖 Статус бота
- ⚙️ Лимиты
- 🧪 Проверка подключения
- 🖥 Открыть PMBOT
- 🚨 Стоп
- 🌐 Язык

Engineering and review-gate labels are not first-level product menu buttons.

## EN Main Menu

The EN product menu is:

- 🔐 Connection
- 💰 Balance
- 📊 Trades
- 📈 PnL
- 🤖 Bot Status
- ⚙️ Limits
- 🧪 Connection Check
- 🖥 Open PMBOT
- 🚨 Stop
- 🌐 Language

## Product Screens

`🔐 Подключение` shows only redacted/presence status:

- API ключи: добавлены/не добавлены
- Private key: добавлен/не добавлен
- Wallet: redacted/missing
- Signature type: present/missing
- Funder: redacted/missing
- L2 auth: not run/ok/blocked/failed
- Значения ключей никогда не показываются

`💰 Баланс` does not invent balances. Without a real read-only balance artifact it says: `Баланс пока не проверен. Запустите read-only проверку подключения.`

`📊 Сделки` says: `Live-сделок пока не было` unless future real ledger/probe artifacts exist.

`📈 PnL` says: `PnL пока недоступен: live-сделок ещё не было.`

`🤖 Статус бота` states review/dry-run mode and that live trading, order submission, signing, and wallet live execution are off.

`⚙️ Лимиты` shows tiny/supervised planned limits from local artifacts when present, otherwise safe placeholders. It does not enable live mode.

`🧪 Проверка подключения` opens the existing safe connection status screen and can expose only the existing read-only/dry-run status action. It does not submit, cancel, sign, or connect a wallet.

`🖥 Открыть PMBOT` opens a marker-driven Mini App button when `PMBOT_TELEGRAM_MINI_APP_URL` is configured and URL-safe. If missing, the runtime text says `Mini App URL не настроен`.

`🚨 Стоп` is a local/status-only placeholder. It does not cancel live orders.

## Manual Verification

From current `master`, restart the runtime from a clean checkout:

```powershell
python -m pm_bot.operator_runner.telegram_operator_runtime
```

Required environment markers:

- `PMBOT_TELEGRAM_BOT_TOKEN`
- `PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS`
- optional `PMBOT_TELEGRAM_MINI_APP_URL`

Expected screenshots:

- `/start` language picker with `🇷🇺 Русский` and `🇬🇧 English`
- RU menu with the ten Russian product buttons above
- EN menu with the ten English product buttons above
- RU connection screen with only redacted/missing/present status
- balance/trades/PnL screens with no fake balance, trade, or PnL values

## Validation

Required validation commands are recorded in `docs/ORCH_PMBOT_TELEGRAM_068C_PRODUCT_UX_START_LANGUAGE_AND_RU_BUTTONS_FIX_RESULT.json` and `pm_bot/trading_core/artifacts/telegram_product_ux_fix_068c/telegram_product_ux_fix_068c_result.json`.

## Safety

068C remains paper/review/dry-run only. It adds no live trading, no signing, no signer instantiation, no signed payload or order generation, no wallet connection, no authenticated Polymarket calls, no fake balances, no fake trades, no fake PnL, no scheduler, no daemon, no background worker, and no browser automation.
