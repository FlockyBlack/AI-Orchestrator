# ORCH-PMBOT-TELEGRAM-068D Mini App Product Dashboard

Task: `ORCH-PMBOT-TELEGRAM-068D-MINI-APP-PRODUCT-DASHBOARD-RU-FIRST-NO-SECRETS-NO-LIVE`

This task upgrades the existing static Telegram Mini App scaffold into a RU-first PMBOT product dashboard shell. The page remains a local/static dashboard and does not add backend calls, forms, scripts, wallet connection, signing, order submission, or order cancellation.

## What Changed

- Reworked `pm_bot/telegram_mini_app/index.html` into a product-style PMBOT dashboard.
- Reworked `pm_bot/telegram_mini_app/styles.css` into a dark fintech interface with responsive cards and bottom navigation.
- Added sections for `Подключение`, `Баланс`, `Сделки`, `PnL`, `Статус`, `Лимиты`, and `Стоп`.
- Added 068D safety/status/menu/UI artifacts under `pm_bot/trading_core/artifacts/telegram_mini_app_product_dashboard_068d/`.
- Added focused regression tests in `pm_bot/tests/test_telegram_mini_app_product_dashboard_068d.py`.

## How To Open Locally

Open the static file directly in a browser:

`pm_bot/telegram_mini_app/index.html`

No dev server is required. The page uses only local `styles.css` and does not require network access.

## Dashboard Contents

- `🔐 Подключение`: redacted/unknown status display for API keys, private key, wallet, signature type, funder, and L2 auth.
- `💰 Баланс`: shows that balance has not been checked and points the operator to a read-only Telegram/CLI check.
- `📊 Сделки`: shows that live trades have not happened and open-order status is unknown unless a read-only probe artifact exists.
- `📈 PnL`: shows that PnL is unavailable until real live trades and reconciliation exist.
- `🤖 Статус бота`: shows live trading, order sending, signing, and wallet execution as disabled with `allowed_for_live=false`.
- `⚙️ Лимиты`: shows planned supervised tiny mode, `Max order <= $1`, `Max orders/day: 1`, and disabled automation.
- `🚨 Стоп`: shows a local emergency stop placeholder and states that live order cancellation is not available in the Mini App.

## Intentionally Not Implemented

- No secret input fields.
- No secret persistence.
- No wallet connection.
- No signing or signer instantiation.
- No signed payload or order generation.
- No order submission.
- No order cancellation.
- No authenticated Polymarket calls.
- No real balance/orders/PnL feed.
- No fake balances, trades, or PnL.
- No scheduler, daemon, background worker, or autonomous loop.
- No full Mini App language switch; RU-first is the current static UI. EN copy/language switching is future work.

## Safety Statement

The 068D Mini App is a static product dashboard shell only. It does not collect, read, store, serialize, or submit secrets. It does not connect wallets, sign payloads, generate orders, submit orders, cancel orders, call authenticated trading endpoints, or enable live trading.

## Future Tasks

- Mini App URL hosting.
- Secure credentials vault.
- Read-only CLOB probe artifact feed.
- Real balance/orders/PnL dashboard after live execution and reconciliation exist.
