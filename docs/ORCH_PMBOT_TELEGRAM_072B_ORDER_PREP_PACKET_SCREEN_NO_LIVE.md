# ORCH-PMBOT-TELEGRAM-072B Order Prep Packet Screen

Task: `ORCH-PMBOT-TELEGRAM-072B-ORDER-PREP-PACKET-SCREEN-NO-LIVE`

This task adds a RU-first Telegram product screen for the first-order preparation packet. The screen uses the title `🧪 Подготовка первого ордера` and stays inside the existing `/order_prep_status` same-message navigation path.

## What It Shows

When a local 072A packet artifact is present, the screen summarizes:

- `Рынок`: `найден` or `не найден`.
- `Token ID`: `выбран` or `требуется выбор`.
- `Аккаунт`: `read-only OK`, `не проверен`, or `ошибка`.
- `L2 auth`: `OK`, `blocked`, or `unknown`.
- `Signer`: `OK`, `не проверен`, or `ошибка`.
- `Approval`: `требуется`, `готов`, or `не найден`.
- `Payload dry-run`: `готов` or `заблокирован`.
- `Live`: always `выключен`.
- `Отправка ордера`: always `выключена`.

If no 072A artifact exists, the screen shows `Пакет подготовки ещё не собран` and keeps all readiness labels conservative.

## Telegram Controls

The 072B packet screen exposes only these buttons:

- `🔄 Обновить`: re-renders `/order_prep_status`.
- `🔎 Найти рынок`: navigates to the existing market discovery view.
- `🧪 Проверить подключение`: navigates to the existing connection-status view.
- `⬅️ Назад`: returns to the home menu.

There are no submit, cancel, signing, wallet, or live-enablement controls. The primary home menu is unchanged and does not add a technical order-prep button.

## Artifact Inputs

The builder reads only local JSON files under `pm_bot/trading_core/artifacts`. It prefers explicit 072A packet names such as:

- `order_prep_packet_072a/latest_order_prep_packet_072a.json`
- `first_order_prep_packet_072a/latest_first_order_prep_packet_072a.json`
- `order_prep_packet_from_discovery_072a/latest_order_prep_packet_from_discovery_072a.json`

It also records whether the legacy 071E status artifact exists, so older 071E status behavior remains available when no generated 072B packet screen artifact is loaded.

## Outputs

Generated under `pm_bot/trading_core/artifacts/telegram_order_prep_packet_screen_072b/`:

- `telegram_order_prep_packet_screen_072b_result.json`
- `latest_telegram_order_prep_packet_screen_072b.json`
- `telegram_order_prep_packet_screen_menu_snapshot_072b.json`
- `telegram_order_prep_packet_screen_safety_snapshot_072b.json`

## Safety Statement

This is a local artifact status screen only. It performs no live trading, no order submit/cancel, no signing, no wallet connection, no authenticated Polymarket calls from Telegram, no browser automation, and no fake balances/trades/PnL. Raw token IDs, account addresses, and secret-like values from source packets are not copied into the Telegram status output.
