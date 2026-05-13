# ORCH-PMBOT-TRADING-MVP-045 Telegram Bot Runtime Wiring for Existing Bot

Task ID: `ORCH-PMBOT-TRADING-MVP-045-TELEGRAM-BOT-RUNTIME-WIRING-FOR-EXISTING-BOT`

This task wires PMBOT operator-control commands to an existing Telegram bot token, such as the operator's Fuzzer-bot. The token stays local in the operator's Windows User environment and is read only when the runtime is explicitly started.

## Safety Posture

- This does not enable trading.
- This does not submit orders.
- This does not connect wallets.
- This does not sign payloads, transactions, or orders.
- This does not call authenticated Polymarket endpoints.
- Telegram `/pause` and `/kill` remain local operator-state markers only.
- `allowed_for_live`, `canary_executable_now`, `live_execution_approved`, `real_execution_available`, `live_connector_enabled`, and `order_submission_enabled` remain false.

## Configure the Existing Bot Token

Set the Telegram bot token from BotFather in the Windows User environment:

```powershell
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_BOT_TOKEN", "TOKEN_FROM_BOTFATHER", "User")
```

The runtime reports only:

```text
Telegram token: configured:redacted
```

It never prints or persists the raw token.

## Configure Allowed Operator IDs

Set the allowed Telegram operator user IDs in the Windows User environment:

```powershell
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS", "123456789", "User")
```

Multiple IDs may be separated by commas, semicolons, or spaces. Startup output reports only the configured count, not raw IDs.

## Optional Mini App URL

If the static Telegram Mini App panel is hosted somewhere safe for Telegram to open, set:

```powershell
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_MINI_APP_URL", "https://example.invalid/pmbot-panel", "User")
```

When configured, `/panel` returns the normal review-only panel status plus an "Open PMBOT Mini App Panel" button. The runtime does not expose Telegram init data or raw secrets.

## Optional Artifact Directory

If PMBOT paper-loop artifacts are available locally, set:

```powershell
[Environment]::SetEnvironmentVariable("PMBOT_ARTIFACT_DIR", "C:\path\to\pmbot\artifacts", "User")
```

The runtime can load local dashboard/panel summaries from that directory and persist Telegram operator-control state markers to `telegram_operator_control_state_043.json`. The persisted state stores hashed operator identifiers only.

## Start the Bot

Open a new terminal after changing Windows User environment variables, then run:

```powershell
python -m pm_bot.operator_runner.telegram_operator_runtime
```

Startup validates:

- `PMBOT_TELEGRAM_BOT_TOKEN`
- `PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS`
- optional `PMBOT_TELEGRAM_MINI_APP_URL`
- optional `PMBOT_ARTIFACT_DIR`

Long polling starts only from this explicit command. Importing the module does not start polling.

## Stop the Bot

Stop the runtime with `Ctrl+C` in the terminal that is running long polling.

## Replace the Bot Later

To replace Fuzzer-bot later, create or choose another Telegram bot and replace only the local token:

```powershell
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_BOT_TOKEN", "TOKEN_FROM_BOTFATHER", "User")
```

No code change is required.

## Supported Commands

The runtime routes incoming Telegram messages to the existing PMBOT operator-control handlers:

```text
/start
/help
/status
/btc
/intent
/risk
/auth
/order
/gonogo
/evidence
/blockers
/pause
/kill
/panel
```

Unauthorized Telegram user IDs receive a safe denial. Authorized users receive review-only PMBOT status/control responses. No command enables live execution or submits orders.

## Runtime Dependency

The runtime imports the Telegram client dependency lazily. If the dependency is missing, startup exits safely with:

```text
Telegram runtime dependency missing
```

Install `python-telegram-bot` in the local operator environment, then rerun the module. Existing tests do not require this dependency and do not call Telegram.

## Troubleshooting

- `Telegram token: missing`: set `PMBOT_TELEGRAM_BOT_TOKEN`, open a new terminal, and rerun.
- `Allowed operator IDs: missing`: set `PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS`, open a new terminal, and rerun.
- `Allowed operator IDs: invalid`: use numeric Telegram user IDs only, separated by commas, semicolons, or spaces.
- `/panel` says Mini App URL is not configured: set `PMBOT_TELEGRAM_MINI_APP_URL` or use the local/static artifact message.
- `/panel` rejects the Mini App URL: use an `https://` or `http://` URL without embedded username/password.
- A user receives `Access denied`: add that Telegram numeric user ID to `PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS` and restart the runtime.
- `Telegram runtime dependency missing`: install `python-telegram-bot` in the local environment used to run PMBOT.
