# ORCH-PMBOT-TRADING-MVP-046E Telegram Operator Runtime UX Smoke Fixes

Task ID: `ORCH-PMBOT-TRADING-MVP-046E-TELEGRAM-OPERATOR-RUNTIME-UX-SMOKE-FIXES`

This task refines Telegram operator runtime messages, smoke diagnostics, and handoff clarity after the real Fuzzer-bot runtime smoke. No trading is enabled.

## Quickstart

Open a fresh PowerShell terminal that has the local operator environment variables, then run the no-network smoke first:

```powershell
python -m pm_bot.operator_runner.telegram_runtime_smoke
```

If the smoke is clean, start the Telegram runtime explicitly:

```powershell
python -m pm_bot.operator_runner.telegram_operator_runtime
```

Stop long polling with `Ctrl+C` in the same terminal.

## No-Network Smoke

Default smoke does not contact Telegram and does not use the bot token on the network:

```powershell
python -m pm_bot.operator_runner.telegram_runtime_smoke
```

Expected sections:

- Environment
- Dependency
- Runtime module
- Mini App
- Safety
- Network check
- Next run command

The smoke reports the Telegram token only as `configured:redacted` or `missing`. Operator IDs are reported by configured count only.

## Optional Network Check

Only this explicit command calls Telegram `getMe`:

```powershell
python -m pm_bot.operator_runner.telegram_runtime_smoke --network-check
```

The token is never printed. A successful check may print the safe bot username returned by Telegram. Failures are categorized with safe labels such as `INVALID_OR_REVOKED_TOKEN`, `TELEGRAM_API_TIMEOUT`, `NETWORK_UNREACHABLE`, or `POLLING_CONFLICT`.

## Runtime Command

Start the real long-polling runtime:

```powershell
python -m pm_bot.operator_runner.telegram_operator_runtime
```

The runtime remains review-only. It does not submit orders, connect wallets, sign payloads, call authenticated Polymarket endpoints, or add autonomous execution.

## Common Errors And Fixes

- 401 Unauthorized: run `python -m pm_bot.operator_runner.telegram_runtime_smoke --network-check`. If it reports `INVALID_OR_REVOKED_TOKEN`, replace `PMBOT_TELEGRAM_BOT_TOKEN` from BotFather, open a new terminal, and rerun smoke. Do not print the token.
- Timeout: if the network check reports `TELEGRAM_API_TIMEOUT`, check local connectivity and Telegram availability, then retry. The no-network smoke still validates local wiring.
- Wrong operator ID: if Telegram replies with access denied, update `PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS` with the correct numeric Telegram user ID, open a new terminal, and restart. Shared logs should mention only the configured count.
- Dependency missing: if smoke reports `python-telegram-bot: missing`, install `python-telegram-bot` in the same Python environment used to run PMBOT, then rerun smoke.
- Mini App URL missing: `/panel` remains usable and shows fallback review-only buttons. Set `PMBOT_TELEGRAM_MINI_APP_URL` later when a hosted Mini App URL is available.
- Another polling instance: if runtime startup reports a polling conflict, stop the other local terminal, service, or bot process using the same token, wait briefly, then restart.

## Telegram UX Notes

`/start` is intentionally concise:

```text
PMBOT Operator Control
Review-only
Live trading disabled
Use buttons below
```

`/panel` attaches `Open PMBOT Mini App` only when `PMBOT_TELEGRAM_MINI_APP_URL` is configured with a safe `https://` or `http://` URL. If the URL is missing, `/panel` says `Mini App URL is not configured yet` and provides safe fallback buttons.

## Safety Statement

- No trading is enabled.
- No real orders are submitted.
- No wallet integration is added.
- No signing is added.
- No authenticated Polymarket calls are added.
- No autonomous execution is added.
- Telegram `/pause` and `/kill` remain local operator-control state markers only.
- The Mini App remains review-only.
- `allowed_for_live` remains false.
- `canary_executable_now` remains false.
- `live_execution_approved` remains false.
- `real_execution_available` remains false.
- `live_connector_enabled` remains false.
- `order_submission_enabled` remains false.
- `resolved_blocker_count` remains 0.
