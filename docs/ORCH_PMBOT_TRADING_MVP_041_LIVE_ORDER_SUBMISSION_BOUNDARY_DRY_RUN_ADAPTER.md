# ORCH-PMBOT-TRADING-MVP-041 Live Order Submission Boundary Dry-Run Adapter

## Purpose

This task adds the final non-executing boundary between the BTC dry-run order intent chain and any future live connector/order submission implementation.

The boundary produces deterministic dry-run submission review receipts for operator inspection. It does not submit orders, call authenticated endpoints, sign payloads, connect to wallets, inspect real secrets, or make the tiny BTC canary executable.

## Boundary Inputs

The adapter accepts review artifacts from the existing tiny BTC canary path:

- BTC market analysis and dry-run order intent from `btc_market_analysis_order_intent.py`
- risk decision and risk control summary from `risk_limit_control_plane.py`
- redacted credential/auth status from `live_credentials_auth_boundary.py`
- operator review and operator signed-intent context, when available
- kill-switch and live blocker matrix context, when available

All inputs are treated as artifacts. They are not used to call external APIs or produce executable order payloads.

## Receipt Output

`pm_bot/trading_core/live_order_submission_boundary.py` emits a deterministic receipt with:

- `schema_version`: `041.v1`
- `boundary_name`: `live_order_submission_boundary_dry_run_adapter`
- BTC market and intent summary fields
- risk decision summary
- auth boundary summary
- operator context summary
- kill-switch summary
- live blocker summary
- refusal and blocker reasons
- static validation and secret-boundary validation

When the BTC intent is valid, the risk decision allows dry-run, and credential state is safely redacted or missing, the receipt status is:

- `dry_run_submission_boundary_review_ready`

This status means review-ready only. It is not a live approval.

## Forced Non-Execution Flags

The receipt and summary force these fields to remain disabled:

- `would_submit_order`: `false`
- `order_submission_enabled`: `false`
- `authenticated_endpoint_enabled`: `false`
- `authenticated_endpoints_enabled`: `false`
- `signing_enabled`: `false`
- `cryptographic_signing_enabled`: `false`
- `wallet_enabled`: `false`
- `wallet_signing_enabled`: `false`
- `allowed_for_live`: `false`
- `live_execution_approved`: `false`
- `real_execution_available`: `false`
- `canary_executable_now`: `false`
- `live_connector_enabled`: `false`

If any input implies real execution, the boundary hard-blocks with:

- `blocked_live_execution_violation`

## Blocked Paths

The adapter produces blocked receipts for:

- missing dry-run order intent
- stale BTC market data
- closed or resolved market data
- non-BTC market data
- risk decisions that do not allow dry-run
- unsafe auth boundary state
- live execution flags appearing anywhere in boundary inputs

Blocked receipts still remain passive review artifacts and never claim submission, fills, execution, balances, prices, PnL, or outcomes.

## Secret Boundary

The static secret boundary now classifies the order submission boundary as non-secret-reading and non-executing.

Receipts and UI summaries may include symbolic review metadata and disabled flags, but they must not include:

- private keys
- mnemonics or seed phrases
- bearer tokens
- API key values
- raw credential values
- auth headers
- signed payloads
- signed orders
- transaction payloads
- executable order payloads

Tests use fake injected credential values only and assert those values are not present in receipts.

## Paper Daily Loop Artifact

The paper daily loop writes:

- `live_order_submission_boundary_041.json`

The dashboard includes a `live_order_submission_boundary_summary` and a `live_order_submission_boundary_section_feed` for operator review.

The loop validation requires the 041 receipt and summary to remain non-executing before the daily run is considered valid.

## Operator UI

The operator UI panel includes a passive `Live Order Submission Boundary` section with:

- boundary status
- dry-run review readiness
- market and intent identifiers
- order submission disabled state
- authenticated endpoint disabled state
- signing disabled state
- wallet disabled state
- live approval and canary executable flags fixed to false
- top refusal and blocker reasons

The UI exposes no executable action and remains a review dashboard only.

## Evidence Bundle And Blocker Matrix

The readiness evidence bundle includes:

- `live_order_submission_boundary_dry_run_adapter`

This evidence item is `review_only` and `execution_enabling: false`.

The live blocker matrix adds unresolved critical blockers for:

- `live_order_submission_boundary_review_only`
- `live_order_submission_boundary_not_live_approval`
- `authenticated_endpoint_required_but_disabled`
- `signing_required_but_disabled`
- `wallet_required_but_disabled`
- `order_submission_boundary_non_executable`

No live blocker is resolved by this task.

## Operator Checklist

For 041 review, verify:

- the 041 receipt exists in the daily loop artifacts
- receipt status is review-ready or explicitly blocked
- `would_submit_order` is false
- `order_submission_enabled` is false
- authenticated endpoints are disabled
- signing is disabled
- wallet usage is disabled
- all live execution flags are false
- no raw secrets appear in JSON, Markdown, HTML, logs, or tests
- blocker matrix `resolved_blocker_count` remains `0`

This checklist does not authorize live execution.
