# ORCH-PMBOT-TELEGRAM-069C Single-Message Product Menu

Task ID: `ORCH-PMBOT-TELEGRAM-069C-SINGLE-MESSAGE-PRODUCT-MENU-NO-LIVE`

## Before / After UX

Before this task, the Telegram surface mixed product labels with internal readiness/debug terms and normal callback presses replied with another message. That made `/start` and button navigation feel noisy.

After this task, `/start` shows one language picker message. Language selection and product navigation use the callback edit renderer, so normal button presses update the same message. If Telegram refuses an edit because a message is too old or not editable, the runtime sends one replacement message as a fallback.

## Expected `/start` Flow

1. `/start` sends only:
   - `🇷🇺 Русский`
   - `🇬🇧 English`
2. Choosing `🇷🇺 Русский` edits the same message to the RU product menu.
3. Choosing `🇬🇧 English` edits the same message to the EN product menu.
4. Product buttons open screens in the same message.
5. `⬅️ Назад` edits the same message back to the main menu.
6. `🌐 Язык` edits the same message back to the language picker.

## RU Menu Screenshot Checklist

The primary RU menu must show only these product buttons:

- `🔐 Подключение`
- `💰 Баланс`
- `📊 Сделки`
- `📈 PnL`
- `⚙️ Лимиты`
- `🤖 Статус`
- `🖥 Mini App`
- `🌐 Язык`
- `🚨 Стоп`

It must not show `DryRun`, `Provider`, `Gate`, `062P`, `063`, `064`, `readiness`, `scaffold`, `runner`, `supervised live enablement`, `static safety`, or `tiny order` in the primary menu.

## Mini App URL Behavior

If `PMBOT_TELEGRAM_MINI_APP_URL` is configured with a safe HTTP/HTTPS URL, the Mini App screen includes an `Открыть PMBOT` / `Open PMBOT` Telegram WebApp button.

If the URL is missing, the Mini App screen says:

`Mini App URL не настроен. Нужно задать PMBOT_TELEGRAM_MINI_APP_URL.`

The Mini App path does not collect or persist secrets.

## Intentionally Not Implemented

- Live trading
- Wallet connection
- Signer instantiation
- Signing or signed payload/order generation
- Order submission
- Order cancellation
- Authenticated Polymarket trading calls
- Fake balances, fake trades, or fake PnL
- Scheduler, daemon, background worker, autonomous loop, or browser automation

## Safety Statement

Telegram controls remain product status/review/dry-run only. This task does not enable real trading, wallet access, signing, authenticated trading actions, order submission, order cancellation, or irreversible operations.

## Artifacts

- `pm_bot/trading_core/artifacts/telegram_single_message_product_menu_069c/telegram_single_message_product_menu_069c_result.json`
- `pm_bot/trading_core/artifacts/telegram_single_message_product_menu_069c/latest_telegram_single_message_product_menu_status_069c.json`
- `pm_bot/trading_core/artifacts/telegram_single_message_product_menu_069c/telegram_single_message_product_menu_ru_snapshot_069c.json`
- `pm_bot/trading_core/artifacts/telegram_single_message_product_menu_069c/telegram_single_message_product_menu_en_snapshot_069c.json`
- `pm_bot/trading_core/artifacts/telegram_single_message_product_menu_069c/telegram_single_message_product_menu_navigation_snapshot_069c.json`
- `pm_bot/trading_core/artifacts/telegram_single_message_product_menu_069c/telegram_single_message_product_menu_safety_snapshot_069c.json`
- `docs/ORCH_PMBOT_TELEGRAM_069C_SINGLE_MESSAGE_PRODUCT_MENU_NO_LIVE_RESULT.json`
