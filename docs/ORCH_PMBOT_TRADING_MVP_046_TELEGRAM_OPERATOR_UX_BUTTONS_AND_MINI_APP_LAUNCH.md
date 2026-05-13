# ORCH-PMBOT-TRADING-MVP-046 Telegram Operator UX Buttons and Mini App Launch

Task ID: `ORCH-PMBOT-TRADING-MVP-046-TELEGRAM-OPERATOR-UX-BUTTONS-AND-MINI-APP-LAUNCH`

This task adds safe Telegram operator UX controls to the existing PMBOT Telegram runtime. The runtime remains explicit long polling only:

```powershell
python -m pm_bot.operator_runner.telegram_operator_runtime
```

## What Changed

- `/start` now renders a concise operator home screen:
  - `PMBOT Operator Control`
  - `Review-only`
  - `Live blocked`
- The command layer now returns a pure testable keyboard model:
  - `TelegramOperatorButton`
  - `TelegramOperatorKeyboard`
  - `TelegramOperatorControlResponse.keyboard`
- The runtime adapter converts the pure keyboard model into Telegram inline buttons.
- Callback queries route back to the same existing safe command handlers.
- `/panel` can attach an `Open PMBOT Mini App` launch button when `PMBOT_TELEGRAM_MINI_APP_URL` is configured.
- Runtime startup can set the Telegram command menu through `set_my_commands` when the installed `python-telegram-bot` version supports it.

## Home Buttons

The `/start` and `/help` screens include the mobile-friendly operator controls:

```text
Status | Go/No-Go
Risk | Blockers
Evidence | Panel
Pause | Kill
```

The labels avoid execution wording such as `BUY`, `SELL`, `TRADE`, `EXECUTE`, and `APPROVE LIVE`.

## Callback Routing

Telegram callbacks map to the existing command handlers:

```text
pmbot:status -> /status
pmbot:btc -> /btc
pmbot:intent -> /intent
pmbot:risk -> /risk
pmbot:auth -> /auth
pmbot:order -> /order
pmbot:gonogo -> /gonogo
pmbot:evidence -> /evidence
pmbot:blockers -> /blockers
pmbot:panel -> /panel
pmbot:pause -> /pause
pmbot:kill -> /kill
```

Unauthorized users are denied on callbacks the same way they are denied on text commands. Denials do not expose raw Telegram user IDs.

## Mini App Launch

Set the optional Mini App URL in the local operator environment:

```powershell
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_MINI_APP_URL", "https://example.invalid/pmbot-panel", "User")
```

After opening a new terminal and starting the runtime, `/panel` attaches a Telegram WebApp button when supported by the Telegram client library. If WebApp button construction is unavailable, the runtime falls back to a URL button with the same label:

```text
Open PMBOT Mini App
```

The runtime never prints or persists Telegram init data, the Telegram bot token, raw operator IDs, private keys, API secrets, or raw credentials.

If `PMBOT_TELEGRAM_MINI_APP_URL` is not configured, `/panel` clearly reports:

```text
Mini App URL is not configured yet
```

It also keeps showing local/static panel artifact availability when `PMBOT_ARTIFACT_DIR` points at generated PMBOT artifacts, and it includes fallback buttons back to Status, Go/No-Go, and Blockers.

## Command Menu

During explicit runtime startup, the runtime attempts to set this Telegram command menu if the installed Telegram library supports it:

```text
/start - Open operator home
/status - PMBOT status
/panel - Mini App panel
/gonogo - Go/No-Go gate
/blockers - Live blockers
/risk - Risk limits
/pause - Local pause marker
/kill - Local kill-switch marker
/help - Help
```

This setup is not performed on import and is covered by fake-client tests.

## Safety Posture

The buttons do not enable trading:

- No button submits an order.
- No button approves live trading.
- No button connects a wallet.
- No button signs payloads, transactions, or orders.
- No button calls authenticated Polymarket endpoints.
- `/pause` and `/kill` remain local Telegram operator-control state markers only.
- `allowed_for_live` remains false.
- `canary_executable_now` remains false.
- `live_execution_approved` remains false.
- `real_execution_available` remains false.
- `live_connector_enabled` remains false.
- `order_submission_enabled` remains false.
- `resolved_blocker_count` remains 0.

## Required Runtime Environment

The runtime still requires the existing explicit Telegram configuration:

```powershell
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_BOT_TOKEN", "TOKEN_FROM_BOTFATHER", "User")
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS", "123456789", "User")
```

Optional:

```powershell
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_MINI_APP_URL", "https://example.invalid/pmbot-panel", "User")
[Environment]::SetEnvironmentVariable("PMBOT_ARTIFACT_DIR", "C:\path\to\pmbot\artifacts", "User")
```

Startup output reports only redacted token/operator status and counts. It does not print raw secrets or raw operator IDs.

## Run

```powershell
python -m pm_bot.operator_runner.telegram_operator_runtime
```

Stop the runtime with `Ctrl+C` in the terminal running long polling.
