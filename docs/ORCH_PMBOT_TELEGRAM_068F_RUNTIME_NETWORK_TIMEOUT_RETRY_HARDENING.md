# ORCH PMBOT Telegram 068F Runtime Network Timeout Retry Hardening

## Scope

068F hardens Telegram runtime startup against transient Telegram API timeout failures during bootstrap/getMe. It keeps the Telegram bot review/status/dry-run only and does not add live trading, order submission, order cancellation, signing, signer instantiation, wallet connection, authenticated Polymarket calls, browser automation, schedulers, daemons, or background trading loops.

## Runtime Network Settings

The runtime now loads these redacted Telegram network settings:

- `PMBOT_TELEGRAM_CONNECT_TIMEOUT_SECONDS`
- `PMBOT_TELEGRAM_READ_TIMEOUT_SECONDS`
- `PMBOT_TELEGRAM_WRITE_TIMEOUT_SECONDS`
- `PMBOT_TELEGRAM_POOL_TIMEOUT_SECONDS`
- `PMBOT_TELEGRAM_BOOTSTRAP_RETRIES`

Defaults:

- connect timeout: `30s`
- read timeout: `30s`
- write timeout: `30s`
- pool timeout: `30s`
- bootstrap retries: `3`

Invalid timeout/retry env values fall back to the default and print a clear config warning. Bot tokens and raw operator IDs are not printed.

## Telegram Request Wiring

When `python-telegram-bot` exposes the official `telegram.request.HTTPXRequest` request layer, the runtime builds redacted timeout-aware request objects and applies them through `ApplicationBuilder.request(...)` and `ApplicationBuilder.get_updates_request(...)`.

The runtime also passes supported timeout and `bootstrap_retries` keyword arguments into `Application.run_polling(...)`. Unsupported kwargs are filtered by inspecting the installed method signature.

## Startup Diagnostics

Startup status now includes:

```text
Telegram network: connect=30s read=30s write=30s pool=30s bootstrap_retries=3
```

If Telegram bootstrap/getMe still exhausts the configured timeouts/retries, the runtime prints:

```text
Telegram API timed out during bootstrap/getMe. Check VPN/firewall/proxy/api.telegram.org or increase PMBOT_TELEGRAM_* timeout env vars.
```

The diagnostic does not include the bot token.

## Smoke Diagnostics

`python -m pm_bot.operator_runner.telegram_runtime_smoke` remains offline-safe by default and does not call Telegram unless explicitly requested.

Optional network diagnostic:

```powershell
python -m pm_bot.operator_runner.telegram_runtime_smoke --network-check
```

This optional check calls Telegram getMe only when requested and keeps the token redacted in URLs and output.

## Manual Operator Run After Merge

From current `master` worktree:

```powershell
python -m pm_bot.operator_runner.telegram_operator_runtime
```

Recommended operator env if needed:

```powershell
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_CONNECT_TIMEOUT_SECONDS", "30", "User")
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_READ_TIMEOUT_SECONDS", "30", "User")
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_WRITE_TIMEOUT_SECONDS", "30", "User")
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_POOL_TIMEOUT_SECONDS", "30", "User")
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_BOOTSTRAP_RETRIES", "3", "User")
```

## Validation

Validation is recorded in `docs/ORCH_PMBOT_TELEGRAM_068F_RUNTIME_NETWORK_TIMEOUT_RETRY_HARDENING_RESULT.json` and `pm_bot/trading_core/artifacts/telegram_runtime_network_timeout_068f/telegram_runtime_network_timeout_068f_result.json`.

## Safety

068F changes Telegram runtime startup diagnostics and network timeout configuration only. Telegram controls remain review/status/dry-run only.
