# ORCH-PMBOT-TRADING-MVP-042 Tiny Live Canary Manual Execution Checklist And Final Go/No-Go Gate

## Purpose

This task adds the final deterministic, review-only operator gate before any future tiny live canary execution can be considered.

The gate consolidates the 037-041 safety chain into one local packet:

- BTC read-only market connector status
- BTC market analysis and dry-run order intent
- risk limit control plane
- live credentials/auth boundary
- live order submission boundary dry-run receipt
- operator signed intent packet context
- readiness evidence bundle
- kill-switch requirements
- unresolved live blocker matrix

The output packet is written by the paper daily loop as:

- `tiny_live_canary_gonogo_gate_042.json`

## What 042 Does

`pm_bot/trading_core/tiny_live_canary_gonogo_gate.py` builds a deterministic manual go/no-go packet with:

- `schema_version`: `042.v1`
- `gate_name`: `tiny_live_canary_manual_execution_checklist_and_final_gonogo_gate`
- `overall_decision`: `NO_GO`
- `decision_level`: `FINAL_MANUAL_REVIEW_ONLY`
- manual execution checklist
- final pre-live checklist
- go requirements for a separate future live-enabling task
- no-go reasons
- unresolved blockers
- operator required actions
- static validation and secret-boundary validation

When unresolved blockers remain, the packet status is:

- `NO_GO_UNRESOLVED_BLOCKERS`

If an input claims live execution, order submission, authenticated endpoints, signing, wallet use, or `GO_FOR_LIVE`, the gate hard-blocks with:

- `HARD_BLOCK_LIVE_EXECUTION_CLAIM`

## What 042 Does Not Do

This task does not:

- enable live trading
- approve live execution
- submit orders
- generate executable order payloads
- call authenticated endpoints
- call Polymarket APIs
- connect wallets
- read private keys, mnemonics, seed phrases, auth tokens, API secrets, or raw credentials
- implement cryptographic signing
- implement wallet signing
- implement transaction signing
- generate signed orders or signed payloads
- add browser automation
- add a scheduler, daemon, or autonomous live trading loop
- resolve live blockers

## Forced Non-Execution Flags

The packet, packet summary, daily loop dashboard, readiness evidence item, and operator UI keep these fields disabled:

- `final_live_enablement_present`: `false`
- `live_execution_approved`: `false`
- `allowed_for_live`: `false`
- `canary_executable_now`: `false`
- `order_submission_enabled`: `false`
- `real_execution_available`: `false`
- `live_connector_enabled`: `false`
- `would_submit_order`: `false`
- `order_submitted`: `false`
- `real_order_submitted`: `false`
- `authenticated_endpoint_enabled`: `false`
- `authenticated_endpoints_enabled`: `false`
- `signing_enabled`: `false`
- `cryptographic_signing_enabled`: `false`
- `wallet_enabled`: `false`
- `wallet_signing_enabled`: `false`
- `execution_enabled`: `false`
- `live_action_exposed`: `false`

The gate never emits `GO_FOR_LIVE`.

## Manual Execution Checklist

The packet includes deterministic operator checklist items requiring manual confirmation that:

- the target BTC market is exactly the intended market
- the market is open, unresolved, and fresh
- the order intent remains dry-run only
- max order notional remains tiny
- daily loss cap remains tiny
- total exposure cap remains tiny
- exactly one market is in scope
- one order/trade per day remains the active policy
- the kill switch exists and is manually reachable
- no scheduler, daemon, or autonomous mode is active
- wallet access, signing, and order submission are disabled
- raw credentials are never displayed
- the operator understands this packet is not live approval

All checklist items start as pending manual operator review. The packet records no approval.

## Paper Daily Loop Integration

When artifacts are enabled, `paper_daily_loop.py` writes:

- `tiny_live_canary_gonogo_gate_042.json`

The daily dashboard includes:

- `tiny_live_canary_gonogo_gate`
- `tiny_live_canary_gonogo_gate_summary`
- `latest_tiny_live_canary_gonogo_gate_path`
- go/no-go checklist counts
- no-go reason count
- unresolved blocker count

Daily loop validation requires the 042 packet to remain non-executing with unresolved blockers and `resolved_blocker_count` equal to `0`.

## Operator UI Integration

`operator_ui_panel_v1.py` adds a passive `Tiny Live Canary Go/No-Go Gate` section with:

- overall decision
- review-only status
- checklist counts
- top no-go reasons
- unresolved blocker count
- resolved blocker count
- explicit human approval required
- no executable action
- live enablement flags fixed to `false`
- latest gate artifact path

The UI action state is read-only inspection only. It exposes no executable live action.

## Readiness Evidence Integration

`live_canary_readiness_evidence_bundle.py` adds:

- `tiny_live_canary_manual_execution_checklist_and_final_gonogo_gate`

The evidence item is:

- `review_only: true`
- `execution_enabling: false`
- `live_approval: false`

The live blocker matrix still remains unresolved. The 042 task adds review visibility; it does not resolve or suppress any live blocker.

## Secret Boundary

`secret_boundary_policy.py` classifies the go/no-go packet as a local, non-secret-reading, redacted-only, non-execution artifact.

The packet may report secret-boundary validation counts and paths. It must not include raw credential values.

## Why This Is Still Not Live Approval

The gate is a final manual review packet, not an authorization mechanism.

It requires explicit human approval for any future live path but does not collect that approval, enable an adapter, unlock credentials, wire signing, or provide an order submission path.

Any future tiny live canary requires a separate operator-approved task that explicitly changes the live boundary and resolves live blockers under review.

## Future Live-Enabling Work Required

A future explicit task would need to handle, at minimum:

- dual-control operator live approval
- out-of-band credential verification without exposing raw secrets
- authenticated endpoint boundary review
- wallet/signing boundary review
- disabled-first order adapter review
- kill-switch wiring to the live boundary and live verification
- proof that no scheduler, daemon, or autonomous trading path is active
- live blocker matrix resolution in separate reviewed steps

Until then, `allowed_for_live`, `canary_executable_now`, `live_execution_approved`, `real_execution_available`, `live_connector_enabled`, and `order_submission_enabled` remain `false`.
