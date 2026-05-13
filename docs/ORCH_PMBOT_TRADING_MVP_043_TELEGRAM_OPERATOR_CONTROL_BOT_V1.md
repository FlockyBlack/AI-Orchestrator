# ORCH-PMBOT-TRADING-MVP-043 Telegram Operator Control Bot v1

## Purpose

Telegram Operator Control Bot v1 is a safe PMBOT operator visibility surface. It lets an authorized operator inspect PMBOT readiness, BTC canary state, risk limits, auth/order boundaries, final go/no-go status, evidence summaries, unresolved blockers, and passive local pause/kill-switch markers.

The bot is review-only. It does not approve live trading and does not create any executable live action.

## Supported Commands

- `/start` identifies PMBOT Operator Control Bot v1 and states the review-only posture.
- `/help` lists commands and safety limits.
- `/status` shows the current PMBOT posture, live-blocked state, canary executable false, and go/no-go status.
- `/btc` shows a saved BTC market snapshot summary when one exists; it does not invent live market values.
- `/intent` shows the BTC dry-run order intent summary; dry-run only.
- `/risk` shows risk limits such as max order, daily loss, exposure, active markets, and max trades/day when available.
- `/auth` shows redacted/missing credential and Telegram config status only.
- `/order` shows live order submission boundary status, with order submission disabled and would-submit false.
- `/gonogo` shows final go/no-go status, no-go reasons, and unresolved blockers.
- `/evidence` shows readiness evidence bundle counts and missing evidence when available.
- `/blockers` shows unresolved blocker counts and top blocker reasons.
- `/pause` records a safe local operator pause marker only.
- `/kill` records a safe local operator kill-switch marker only.

## What It Does Not Do

- It does not enable live trading.
- It does not submit, place, cancel, or transmit orders.
- It does not connect wallets.
- It does not read private keys, mnemonics, seed phrases, Telegram bot tokens, API secrets, or auth tokens.
- It does not sign payloads, orders, or transactions.
- It does not call authenticated Polymarket endpoints.
- It does not create schedulers, daemons, background workers, or autonomous trading loops.
- It does not fetch live market values from Telegram command handlers.

## Auth and Allowed Operators

The Telegram bot token is never hardcoded. PMBOT surfaces token configuration only as `missing` or `configured_redacted`.

Allowed operator user IDs are configured outside the artifact. Output surfaces only whether allowed IDs are configured and how many are configured. Raw operator IDs are not printed or persisted. If an operator identifier must be recorded in local state, only a deterministic hash is stored.

Unauthorized users receive a safe denial message with no raw credential or operator-ID detail.

## Pause and Kill-Switch State

`/pause` and `/kill` update only the local Telegram operator-control state artifact:

`telegram_operator_control_state_043.json`

These commands do not modify trading execution because this build has no live execution path. `/kill` does not cancel orders or call authenticated endpoints. The state is reflected passively in `/status`, the paper daily dashboard, and the operator UI panel.

## Not Live Approval

This bot is evidence and operator visibility only. It sets:

- `review_only: true`
- `execution_enabling: false`
- `live_approval: false`
- `allowed_for_live: false`
- `canary_executable_now: false`
- `live_execution_approved: false`
- `real_execution_available: false`
- `live_connector_enabled: false`
- `order_submission_enabled: false`

The readiness evidence bundle includes `telegram_operator_control_bot_v1` only as review evidence. It does not resolve live blockers.

## Future Telegram Mini App

A future Telegram Mini App could add richer read-only dashboards, structured approval-review packets, signed-in operator identity display, and clearer artifact navigation. That future work must remain separately gated and still must not enable live execution unless an explicit future operator-approved task changes the safety boundary.
