# ORCH-PMBOT-TRADING-MVP-044 Telegram Mini App Operator Panel v1

## Purpose

This task adds a deterministic, static Telegram Mini App operator panel layer for PMBOT. The panel is a review surface for PMBOT status, BTC canary state, risk limits, auth/order boundaries, the final go/no-go state, unresolved blockers, readiness evidence, and Telegram operator pause/kill markers.

The implementation builds on the Telegram Operator Control Bot v1 from 043/043B. The bot can now return a safe `/panel` message with local/static artifact availability and placeholder Mini App URL/init-data status, without exposing tokens, operator IDs, or raw Telegram init data.

## What It Does

- Builds a pure Python render model with `build_telegram_mini_app_panel_model(...)`.
- Renders deterministic local HTML with `render_telegram_mini_app_panel_html(model)`.
- Emits JSON and HTML artifacts from the paper daily loop:
  - `telegram_mini_app_operator_panel_044.json`
  - `telegram_mini_app_operator_panel_044.html`
- Adds a passive "Telegram Mini App Operator Panel" section to `operator_ui_panel_v1`.
- Adds readiness evidence item `telegram_mini_app_operator_panel_v1`.
- Extends the secret boundary policy for Telegram Mini App URL/init-data related sensitive values.

## What It Does Not Do

- It does not enable live trading.
- It does not submit orders.
- It does not connect wallets.
- It does not sign payloads or transactions.
- It does not call authenticated Polymarket endpoints.
- It does not validate real Telegram init data.
- It does not start a web server, scheduler, daemon, background worker, or autonomous loop.
- It does not add BUY/SELL/TRADE controls or side-selection UI.

All Mini App content is generated from deterministic local data already used by the paper daily loop and operator review artifacts.

## Review-Only Design

The panel forces live execution flags to false:

- `allowed_for_live: false`
- `canary_executable_now: false`
- `live_execution_approved: false`
- `real_execution_available: false`
- `live_connector_enabled: false`
- `order_submission_enabled: false`
- `would_submit_order: false`

Telegram pause and kill states remain local operator-state markers only. They do not cancel orders, mutate wallets, call APIs, or modify an execution adapter.

## Relationship To Telegram Operator Control Bot v1

The 043 bot remains a passive command surface. This task adds `/panel`, which reports whether the static Mini App panel artifacts are available and where the local artifacts are expected. It only reports redacted/missing Mini App URL/init-data status and does not expose raw Telegram bot tokens, raw init data, or raw operator IDs.

## Future Server-Hosted Mini App Work

A future task may add a server-hosted Mini App preview and authenticated Telegram init-data validation. That future work must remain separately operator-approved and should preserve these gates:

- raw Telegram init data is never stored or rendered
- bot tokens and operator IDs remain redacted or hashed
- validation is separated from order execution
- live execution remains disabled until a separate approved live enablement task
- no wallet, signing, or order submission path is introduced by the UI layer

This task intentionally stops at static local HTML/JSON artifacts so it remains testable without network calls or a real Telegram environment.

## Validation

Focused tests are in `pm_bot/tests/test_telegram_mini_app_operator_panel_044.py`. They cover model sections, deterministic rendering, safe HTML, forced-false live flags, redaction, paper daily-loop artifacts, operator UI integration, evidence bundle integration, and safe `/panel` behavior.
