# ORCH PMBOT Trading MVP 037 Risk Limit Control Plane

Task ID: `ORCH-PMBOT-TRADING-MVP-037-RISK-LIMIT-CONTROL-PLANE-DAILY-LOSS-EXPOSURE-MARKET-CAPS`

## Purpose

This task adds a deterministic PMBOT Risk Limit Control Plane for proposed order intents. It is the bridge from passive readiness and UI review toward a future controlled live MVP path, but it does not enable real execution.

The control plane evaluates an intent, current exposure, current daily loss state, and live-readiness gates, then returns one of:

- `ALLOW_DRY_RUN`
- `BLOCK`
- `HALT`
- `REVIEW_ONLY`

In this build, `allowed_for_live` is always `false`.

## Non-Execution Boundary

The control plane is pure and local. It performs no network calls, wallet calls, signing, order placement, authenticated endpoint calls, browser automation, scheduler work, or autonomous execution.

The following remain forced false:

- `live_execution_approved`
- `canary_executable_now`
- `real_execution_available`
- `live_connector_enabled`
- `allowed_for_live`

## Risk Policy Schema

The default policy is intentionally tiny and conservative:

- `max_daily_loss_usd`: `5.0`
- `max_total_exposure_usd`: `10.0`
- `max_market_exposure_usd`: `5.0`
- `max_order_notional_usd`: `1.0`
- `max_orders_per_day`: `1`
- `max_trades_per_day`: `1`
- `max_active_markets`: `1`
- `cooldown_after_loss_minutes`: `30`
- `halt_on_stale_market_data`: `true`
- `max_market_data_age_seconds`: `300`
- `halt_on_audit_mismatch`: `true`
- `halt_on_kill_switch`: `true`
- `halt_on_missing_operator_intent`: `true`
- `halt_on_missing_readiness_evidence`: `true`
- `halt_on_unresolved_critical_blockers`: `true`
- `halt_on_disabled_live_connector`: `true`
- `halt_on_live_execution_not_approved`: `true`
- `halt_on_canary_not_executable`: `true`
- `halt_on_real_execution_unavailable`: `true`
- `allowed_market_ids`: `["btc-one-market-demo-market"]`
- `allowed_market_slugs`: `["btc-one-market-demo"]`
- `allowed_market_tags`: `["BTC", "BITCOIN"]`
- `review_only_until_live_gate`: `true`

These are limits only. They are not live approval.

## Order Intent Schema

`RiskLimitOrderIntent` is an intent object only. It contains:

- `intent_id`
- `market_id`
- `market_slug`
- `market_tag`
- `market_category`
- `side_label`
- `notional_usd`
- `quantity`
- `limit_price`
- `intent_source`
- `created_at`
- `dry_run_only`
- `operator_intent_reference`
- `readiness_evidence_reference`
- `audit_replay_reference`
- `ui_panel_reference`

It does not contain executable submission material, signing material, transaction material, keys, auth headers, or endpoint payloads.

## Decision Behavior

The evaluator enforces:

- order notional cap
- total exposure cap
- market exposure cap
- daily loss halt
- daily order count cap
- daily trade count cap
- active market cap
- cooldown after loss
- stale market data halt
- audit mismatch halt
- kill-switch halt
- missing operator intent block
- missing readiness evidence block
- unresolved critical blockers halt
- live connector disabled as a live blocker
- live approval false as a live blocker
- canary executable false as a live blocker
- real execution unavailable as a live blocker

If any halt reason is present, the decision is `HALT`. If there are no halt reasons but limit or evidence violations exist, the decision is `BLOCK`. If the intent is dry-run-only and all dry-run gates pass, the decision is `ALLOW_DRY_RUN`. Non-dry-run intents remain `REVIEW_ONLY` or halted because live gates are unavailable.

## BTC One-Market Demo Preparation

The default policy includes BTC/Bitcoin tags and one placeholder whitelisted BTC market. A BTC-tagged dry-run intent for that whitelist can pass numeric limits and return `ALLOW_DRY_RUN`.

The same decision still has:

- `allowed_for_live`: `false`
- `live_execution_approved`: `false`
- `canary_executable_now`: `false`
- `real_execution_available`: `false`
- `live_connector_enabled`: `false`

No Polymarket connector is added in this task.

## UI Integration

`pm_bot/operator_runner/operator_ui_panel_v1.py` now surfaces a Risk Control Plane section and summary:

- control plane status
- policy ID
- mode
- daily loss cap
- total exposure cap
- market exposure cap
- order notional cap
- daily order and trade caps
- active market cap
- allowed market tags
- latest decision status
- violation and halt counts
- dry-run allowance
- live allowance forced false

The UI remains read-only and non-execution.

## Paper Daily Loop Integration

`pm_bot/operator_runner/paper_daily_loop.py` now builds the default risk policy, evaluates the latest dry-run candidate when one exists, and exposes:

- `risk_control_plane_summary`
- `default_risk_limit_policy_summary`
- `latest_risk_limit_decision`
- `risk_limit_panel_feed`

This is passive dashboard output only. Paper simulator fill behavior is unchanged.

## Evidence Bundle Integration

`pm_bot/trading_core/live_canary_readiness_evidence_bundle.py` now includes the `risk_limit_control_plane` evidence item. The item is review-ready when policy evidence is present and execution-enabling remains false.

The evidence bundle remains review-only and is not live approval.

## Blocker Matrix Integration

The live blocker matrix now includes additional unresolved critical blockers:

- `risk_limit_control_plane_review_only`
- `risk_limits_not_live_enforced_against_real_connector`
- `btc_market_connector_not_configured`
- `live_order_adapter_not_enabled`
- `real_execution_still_unavailable`

No existing live blockers are resolved or reduced.

## Secret Boundary

The static secret boundary now has helpers for:

- risk limit policy
- risk limit order intent
- risk limit decision
- risk control UI summary

It rejects secret, signing, transaction, auth, and executable order payload field names in risk payloads.

## Next Steps

Recommended next task: `ORCH-PMBOT-TRADING-MVP-037B-MERGE-RISK-LIMIT-CONTROL-PLANE-INTO-MASTER`.

After merge, the next product step should be a read-only BTC/Bitcoin market connector contract that remains unauthenticated, local-artifact-first, and non-execution. A later tiny live canary task must separately prove that every future order intent passes this risk control plane before any real connector can be considered.
