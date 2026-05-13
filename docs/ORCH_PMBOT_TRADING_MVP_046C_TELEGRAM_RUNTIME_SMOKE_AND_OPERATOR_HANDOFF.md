# ORCH-PMBOT-TRADING-MVP-046C Telegram Runtime Smoke and Operator Handoff

Task ID: `ORCH-PMBOT-TRADING-MVP-046C-TELEGRAM-RUNTIME-SMOKE-AND-OPERATOR-HANDOFF`

This handoff verifies the local PMBOT Telegram operator runtime after 046B. It is for the existing Fuzzer-bot token stored in local environment variables. It does not enable live trading, submit orders, connect wallets, sign anything, call authenticated Polymarket endpoints, or add autonomous execution.

## Safety Posture

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

## Verify Environment Variables Safely

Open a fresh PowerShell window after changing Windows User environment variables. Check only redacted status and counts:

```powershell
if ([string]::IsNullOrWhiteSpace($env:PMBOT_TELEGRAM_BOT_TOKEN)) {
  "PMBOT_TELEGRAM_BOT_TOKEN: missing"
} else {
  "PMBOT_TELEGRAM_BOT_TOKEN: configured:redacted"
}

$operatorIds = @($env:PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS -split "[,;\s]+" | Where-Object { $_ })
"PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS: configured count:$($operatorIds.Count)"

if ([string]::IsNullOrWhiteSpace($env:PMBOT_TELEGRAM_MINI_APP_URL)) {
  "PMBOT_TELEGRAM_MINI_APP_URL: missing"
} else {
  "PMBOT_TELEGRAM_MINI_APP_URL: configured:redacted"
}
```

Do not paste, print, or commit the raw Telegram bot token. Do not include raw operator IDs in shared logs.

## Run No-Network Smoke

The default smoke command does not contact Telegram:

```powershell
python -m pm_bot.operator_runner.telegram_runtime_smoke
```

Expected output includes:

- `Telegram token: configured:redacted` or `missing`
- `Allowed operator IDs: configured count:N` or `missing`
- `Mini App URL: configured`, `missing`, or `configured_invalid`
- `python-telegram-bot: installed` or `missing`
- `Runtime module import: ok`
- `Safety flags expected false: ok`
- `Handoff checklist: docs/ORCH_PMBOT_TRADING_MVP_046C_TELEGRAM_RUNTIME_SMOKE_AND_OPERATOR_HANDOFF.md`

For a redacted JSON version:

```powershell
python -m pm_bot.operator_runner.telegram_runtime_smoke --json
```

## Optional Network Check

Only when explicitly requested, the smoke helper calls Telegram `getMe` with the configured bot token:

```powershell
python -m pm_bot.operator_runner.telegram_runtime_smoke --network-check
```

The output still does not print the token. It reports only:

- Telegram API reachable: `true` or `false`
- getMe ok: `true` or `false`
- Bot username when Telegram returns one
- Safe error category such as `unauthorized`, `timeout`, `network_error`, `rate_limited`, or `telegram_http_error`

Use this only after the no-network smoke has passed.

## Run Telegram Runtime

Start the real Telegram long-polling runtime explicitly:

```powershell
python -m pm_bot.operator_runner.telegram_operator_runtime
```

Startup validates the Telegram token and allowed operator IDs, then starts long polling. Importing the runtime module does not start polling.

## Stop Telegram Runtime

Stop the runtime with `Ctrl+C` in the same terminal that is running long polling.

The runtime catches this as an operator stop and exits without enabling live execution.

## Expected Telegram Behavior

`/start` should show:

```text
PMBOT Operator Control
Review-only
Live blocked
```

It should include safe buttons:

```text
Status | Go/No-Go
Risk | Blockers
Evidence | Panel
Pause | Kill
```

These buttons route to the existing review-only command handlers. They do not approve live trading, submit orders, connect wallets, sign payloads, or call authenticated endpoints.

## Expected `/panel` Behavior

When `PMBOT_TELEGRAM_MINI_APP_URL` is missing, `/panel` reports that the Mini App URL is not configured and shows local/static panel artifact availability when `PMBOT_ARTIFACT_DIR` points at generated artifacts.

When `PMBOT_TELEGRAM_MINI_APP_URL` is configured with a safe `https://` or `http://` URL, `/panel` attaches an `Open PMBOT Mini App` button. The button opens the review-only Mini App surface. It does not expose Telegram init data, raw token values, raw operator IDs, or any execution action.

## Set Mini App URL Later

Set or replace the optional Mini App URL in Windows User environment variables:

```powershell
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_MINI_APP_URL", "https://example.invalid/pmbot-panel", "User")
```

Open a new terminal, rerun the no-network smoke, then restart the Telegram runtime.

## Troubleshooting

- Missing dependency: if smoke reports `python-telegram-bot: missing`, install `python-telegram-bot` in the same local Python environment used to run PMBOT, then rerun the smoke.
- Invalid token / 401 Unauthorized: rerun `python -m pm_bot.operator_runner.telegram_runtime_smoke --network-check`. If it reports `unauthorized`, replace `PMBOT_TELEGRAM_BOT_TOKEN` with the current Fuzzer-bot token from BotFather, open a new terminal, and rerun smoke. Do not print the token.
- Telegram timeout: if the network check reports `timeout`, check local connectivity and Telegram availability, then retry. The no-network smoke remains valid for local wiring.
- Wrong operator ID: if Telegram replies `Access denied`, add the correct numeric Telegram user ID to `PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS`, open a new terminal, and restart the runtime. Shared logs should mention only the configured count.
- Another polling process already running: Telegram may reject polling when another process is already using the same bot token. Stop the other local terminal, service, or bot process, wait briefly, then restart this runtime.
- Mini App URL missing: `/panel` remains usable as a review-only panel status. Set `PMBOT_TELEGRAM_MINI_APP_URL` later if a hosted Mini App URL is available.
- Mini App URL rejected: use only `https://` or `http://` URLs without embedded username/password.

## Commands

No-network smoke:

```powershell
python -m pm_bot.operator_runner.telegram_runtime_smoke
```

Optional explicit Telegram `getMe` check:

```powershell
python -m pm_bot.operator_runner.telegram_runtime_smoke --network-check
```

Runtime:

```powershell
python -m pm_bot.operator_runner.telegram_operator_runtime
```
