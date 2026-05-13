# ORCH-PMBOT-TRADING-MVP-048 Authenticated Polymarket Connector Scaffold

Task 048 adds a dry-run-only authenticated Polymarket connector scaffold for future PMBOT tiny supervised live canary preparation. The scaffold defines the future connector contract, capability report, preflight validation, dry-run request/response shapes, redacted credential presence summary, and operator-facing blocker reasons.

## What It Does

- Defines `pm_bot.trading_core.authenticated_polymarket_connector`.
- Reports the connector as review-only and dry-run-only.
- Forces authenticated connector capability flags to false:
  - `authenticated_polymarket_enabled`
  - `network_calls_enabled`
  - `authenticated_calls_enabled`
  - `live_connector_enabled`
  - `order_submission_enabled`
  - `signing_enabled`
  - `wallet_signing_enabled`
  - `real_execution_available`
- Summarizes credential presence as `missing` or `configured_redacted` only.
- Refuses simulated authenticated requests with `DRY_RUN_REFUSED`.
- Emits `authenticated_polymarket_connector_scaffold_048.json` from the paper daily loop.
- Adds passive review-only evidence, go/no-go, dashboard, and operator UI integration.

## What It Does Not Do

- It does not call Polymarket network endpoints.
- It does not call authenticated endpoints.
- It does not submit, place, transmit, or simulate real orders.
- It does not create order IDs, fills, executions, balances, prices, PnL, or live results.
- It does not implement cryptographic signing, wallet signing, transaction signing, or signed payload generation.
- It does not add wallet integration.
- It does not read or emit raw credential values.
- It does not add browser automation, a scheduler, a daemon, or autonomous live trading.

## Credential Boundary

The scaffold recognizes these review-only configuration concepts:

- `PMBOT_AUTHENTICATED_POLYMARKET_ENABLED`
- `PMBOT_POLYMARKET_API_KEY_CONFIGURED`
- `PMBOT_POLYMARKET_API_SECRET_CONFIGURED`
- `PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED`

If raw environment variables are present in a supplied mapping, the scaffold reduces them to presence-only metadata and emits only `configured_redacted`. Raw values are never printed, persisted, returned in JSON, or rendered in UI summaries.

## Why Authenticated Calls Remain Disabled

This task is only a scaffold. Authenticated calls remain disabled because the repository still lacks separately approved live connector implementation work, credential loading policy, signing design, wallet custody controls, order submission adapter, kill-switch verification, and operator live approval workflow.

The following flags remain false by contract:

- `authenticated_polymarket_enabled`
- `live_connector_enabled`
- `order_submission_enabled`
- `wallet_signing_enabled`
- `allowed_for_live`
- `canary_executable_now`
- `live_execution_approved`
- `real_execution_available`

`resolved_blocker_count` remains `0`; live blockers remain unresolved.

## Future Live Connector Requirements

A later explicit live connector task would need to implement and review all of the following before any live behavior is available:

- credential loading and redaction policy with no raw values in artifacts
- authenticated request adapter with all tests mocked
- wallet custody and funding policy
- signing boundary and signing tests
- order submission boundary and refusal-first tests
- kill-switch verification against the live adapter boundary
- operator approval workflow for tiny canary execution
- audit/replay records for every execution-relevant decision

That later task must be separately operator-approved. This scaffold does not enable live trading.
