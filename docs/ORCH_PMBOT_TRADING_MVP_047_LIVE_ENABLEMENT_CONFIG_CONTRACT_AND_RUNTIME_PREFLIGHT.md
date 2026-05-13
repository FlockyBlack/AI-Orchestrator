# ORCH-PMBOT-TRADING-MVP-047 Live Enablement Config Contract And Runtime Preflight

## Purpose

This task adds a deterministic PMBOT live enablement configuration contract and runtime preflight artifact for future tiny supervised live canary review.

It does not enable live trading. It does not submit orders, connect wallets, sign payloads, call authenticated Polymarket endpoints, or expose any executable live action. The contract is review-only and keeps every live execution path blocked by default.

## Module

The contract lives in:

`pm_bot/trading_core/live_enablement_config.py`

The main builders are:

- `build_live_enablement_config_preflight`
- `build_live_enablement_config_preflight_from_env`
- `summarize_live_enablement_config_preflight`
- `validate_live_enablement_config_preflight`

The daily paper loop emits:

`live_enablement_config_preflight_047.json`

## Environment Contract

The preflight reads only these whitelisted non-secret configuration keys:

- `PMBOT_LIVE_MODE`
- `PMBOT_LIVE_CANARY_ENABLED`
- `PMBOT_ORDER_SUBMISSION_ENABLED`
- `PMBOT_AUTHENTICATED_POLYMARKET_ENABLED`
- `PMBOT_WALLET_SIGNING_ENABLED`
- `PMBOT_MAX_ORDER_NOTIONAL_USD`
- `PMBOT_DAILY_LOSS_CAP_USD`
- `PMBOT_TOTAL_EXPOSURE_CAP_USD`
- `PMBOT_MAX_LIVE_TRADES_PER_DAY`
- `PMBOT_ALLOWED_MARKET_SLUGS` or `PMBOT_ALLOWED_MARKET_IDS`
- `PMBOT_REQUIRE_MANUAL_OPERATOR_APPROVAL`
- `PMBOT_REQUIRE_KILL_SWITCH_READY`

Boolean parsing is strict and case-insensitive. Accepted values are:

- true values: `true`, `1`, `yes`
- false values: `false`, `0`, `no`

Invalid boolean strings block the preflight.

Numeric risk limits must be finite positive values. `PMBOT_MAX_LIVE_TRADES_PER_DAY` must be a positive whole number. Zero, negative, missing, non-finite, or non-numeric values block the preflight.

Market scope must use exactly one of `PMBOT_ALLOWED_MARKET_SLUGS` or `PMBOT_ALLOWED_MARKET_IDS`, and it must contain exactly one BTC-related market value. Multiple markets, no markets, both env vars together, or a non-BTC value block the preflight.

## Safe Review-Only Example

This example can produce `REVIEW_ONLY_PREFLIGHT_READY`, but it still cannot enable live execution:

```text
PMBOT_LIVE_MODE=false
PMBOT_LIVE_CANARY_ENABLED=false
PMBOT_ORDER_SUBMISSION_ENABLED=false
PMBOT_AUTHENTICATED_POLYMARKET_ENABLED=false
PMBOT_WALLET_SIGNING_ENABLED=false
PMBOT_MAX_ORDER_NOTIONAL_USD=1
PMBOT_DAILY_LOSS_CAP_USD=1
PMBOT_TOTAL_EXPOSURE_CAP_USD=1
PMBOT_MAX_LIVE_TRADES_PER_DAY=1
PMBOT_ALLOWED_MARKET_SLUGS=btc-one-market-demo
PMBOT_REQUIRE_MANUAL_OPERATOR_APPROVAL=true
PMBOT_REQUIRE_KILL_SWITCH_READY=true
```

Even with this complete review-only configuration, the final output remains:

- `allowed_for_live: false`
- `canary_executable_now: false`
- `live_execution_approved: false`
- `real_execution_available: false`
- `live_connector_enabled: false`
- `order_submission_enabled: false`
- `authenticated_polymarket_enabled: false`
- `wallet_signing_enabled: false`
- `resolved_blocker_count: 0`

## Statuses

The preflight may emit only these statuses:

- `CONFIG_MISSING_BLOCKED`
- `CONFIG_INVALID_BLOCKED`
- `LIVE_FLAGS_REQUESTED_BUT_BLOCKED`
- `REVIEW_ONLY_PREFLIGHT_READY`

It never emits:

- `LIVE_READY`
- `GO_FOR_LIVE`
- `EXECUTION_ENABLED`
- `ORDER_SUBMISSION_ENABLED`

## Why Defaults Are Blocked

Missing config produces `CONFIG_MISSING_BLOCKED` because live readiness must be impossible by accident. An empty environment cannot imply live intent, risk limits, operator approval, kill-switch readiness, or market scope.

The daily paper loop intentionally emits a missing-config blocked preflight by default. That artifact makes the missing live enablement contract visible without reading broad environment state or enabling any future live path.

## Why True Live Flags Remain Blocked

If any live/execution/auth/signing flag is set true, the preflight reports `LIVE_FLAGS_REQUESTED_BUT_BLOCKED`. It records that future live was requested, but task 047 explicitly blocks execution.

This is deliberate. A config contract can make operator intent visible, but it cannot approve live execution. Future live enabling requires a separate explicit operator-approved task.

## Secret Boundary

The live enablement config keys are classified as non-secret config. The module must not parse or emit private keys, wallet keys, mnemonics, seed phrases, API secrets, auth tokens, Telegram tokens, Telegram init data, signed payloads, or raw credentials.

If future config adds sensitive categories, artifacts must redact values and expose only missing/configured status.

## Integration Points

The preflight is included passively in:

- live canary readiness dashboard summaries
- live canary readiness evidence bundle
- live canary replay/governance summary
- tiny live canary go/no-go packet
- paper daily loop artifact output
- operator UI panel v1
- secret boundary policy

All integrations keep live blockers unresolved and keep execution fields false.

## Future Live-Enabling Task Requirements

A future task would need separate explicit approval before any live canary can be considered. At minimum, it must address:

- dual-control human live approval
- live credential handling without raw secret exposure
- authenticated endpoint boundary review
- wallet/signing boundary review without accidental signing
- disabled-first order adapter design
- kill switch wired to any future live adapter boundary
- all live blockers resolved in reviewed tasks
- no autonomous trading or scheduler path unless separately approved

Task 047 does none of that. It only defines the review-only config contract and blocked runtime preflight.
