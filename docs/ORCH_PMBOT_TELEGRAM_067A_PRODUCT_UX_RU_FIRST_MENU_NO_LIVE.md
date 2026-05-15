# ORCH-PMBOT-TELEGRAM-067A Product UX RU-First Menu No Live

## Summary

This task changes the Telegram bot from an engineering/review-first surface into a user-facing PMBOT control center while keeping all execution boundaries closed.

The default visible language is Russian. English remains available through `/en`, and Russian can be selected with `/ru`. `/language` shows both language choices.

## Main Menu

Russian default menu:

- 🏠 Главная
- 🔐 Подключение
- 💰 Баланс
- 📊 Сделки
- 📈 PnL
- 🤖 Статус бота
- ⚙️ Лимиты
- 🚨 Стоп
- 🌐 Язык

English menu:

- Home
- Connection
- Balance
- Trades
- PnL
- Bot Status
- Limits
- Stop
- Language

## Screens

`Подключение / Connection` shows redacted presence states only:

- API credentials: present/missing
- private key: present/missing
- wallet address: redacted/missing
- signature type: present/missing
- funder address: redacted/missing
- auth probe: not implemented yet / pending future probe

`Баланс / Balance` does not show a fake balance. It says: `Баланс пока не проверен: read-only CLOB probe ещё не реализован`.

`Сделки / Trades` does not show fake trades or orders. It says: `Сделок пока нет: live-торговля не запускалась`.

`PnL` does not show fake PnL. It says: `PnL пока недоступен: live-сделок не было`.

`Статус бота / Bot Status` reports `dry-run/review-only`, `allowed_for_live=false`, live trading disabled, order submission disabled, signing disabled, and wallet execution disabled.

`Стоп / Stop` is a local status placeholder only. It does not submit or cancel orders.

## Safety

This implementation does not enable:

- live trading
- wallet connection
- private-key reads
- signing or signer instantiation
- order submission
- order cancellation
- authenticated Polymarket calls
- fake balance, trade, or PnL data
- scheduler, daemon, background worker, or autonomous loop
- browser automation

Legacy review/dry-run internals remain callable where needed for existing tests and operator compatibility, but they are not primary main-menu labels.

## Artifacts

Deterministic artifacts are written under:

`pm_bot/trading_core/artifacts/telegram_product_ux_067a/`

- `telegram_product_ux_067a_result.json`
- `latest_telegram_product_ux_status_067a.json`
- `telegram_product_ux_menu_snapshot_067a.json`
- `telegram_product_ux_i18n_snapshot_067a.json`
- `telegram_product_ux_safety_snapshot_067a.json`

Focused tests:

`python -m pytest pm_bot/tests/test_telegram_product_ux_067a.py`
