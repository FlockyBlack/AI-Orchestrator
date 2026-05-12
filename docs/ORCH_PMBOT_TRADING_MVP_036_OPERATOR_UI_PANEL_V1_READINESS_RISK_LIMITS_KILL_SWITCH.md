# ORCH PMBOT Trading MVP 036 Operator UI Panel v1

## Purpose

Operator UI Panel v1 is a local, static visibility surface for PMBOT paper-mode and future-canary readiness review. It consolidates the readiness evidence bundle, live blocker matrix, risk-limit visibility, kill-switch status, paper summary, operator packets, and audit replay status into one deterministic payload with Markdown and HTML renderers.

The panel is not a live execution console. It does not connect to wallets, signing systems, authenticated endpoints, external APIs, background workers, schedulers, or live order paths.

## What The Panel Shows

- Current execution posture: `paper/dry-run/live-disabled/future-canary-review`
- Paper trading status and paper exposure/PnL fields when available
- Readiness evidence bundle status, evidence item count, missing evidence count, and latest reference
- Live blocker matrix counts, unresolved blocker reasons, and top blocker IDs
- Risk-limit configuration or review placeholders
- Kill-switch requirements, live-verification status, and current block state
- Operator approval packet status and dry-run operator intent status
- Audit replay status and mismatch visibility
- Next gates required before any future live-canary task

## What The Panel Does Not Do

- It does not approve live execution.
- It does not make a canary executable.
- It does not enable the live connector.
- It does not add real risk-control execution gates.
- It does not submit orders, transactions, or any live request.
- It does not inspect or read environment secrets.
- It does not provide market recommendations, probability, EV, edge, confidence, or side-selection as live trading advice.

The following fields are forced false by the panel builder and validator:

- `live_execution_approved`
- `canary_executable_now`
- `real_execution_available`
- `live_connector_enabled`

## Section Schema

The panel payload contract is `pmbot_operator_ui_panel.v1`. It contains these required sections:

- `header_execution_posture`
- `readiness_evidence_bundle`
- `live_blockers`
- `risk_limits`
- `kill_switch`
- `paper_trading_summary`
- `operator_packets`
- `audit_replay`
- `next_gates`

Each section is a passive `OperatorUIPanelSection` with deterministic metrics, warnings, and optional action states. Action states are read-only or dry-run review states with `execution_enabled=false` and `live_action_exposed=false`.

## Readiness And Evidence Display

The readiness evidence section reports:

- `readiness_evidence_bundle_status`
- `evidence_item_count`
- `missing_required_evidence_count`
- `latest_readiness_evidence_bundle_path`
- `readiness_bundle_is_not_live_approval=true`

The readiness bundle remains a review artifact. It does not reduce blocker severity and does not authorize live execution.

## Blocker Display

The blocker section reports:

- total blockers
- critical blockers
- unresolved blockers
- resolved blockers
- top blocker IDs and reasons
- `all_blockers_unresolved=true`

The blocker display is intentionally conservative. It explains why live execution remains blocked and keeps all live connector blockers unresolved.

## Risk Limit Display

The risk-limit section displays configured values when present and review placeholders where the future live control plane is not configured:

- `max_daily_loss_usd`
- `max_total_exposure_usd`
- `max_market_exposure_usd`
- `max_order_notional_usd`
- `max_market_count`
- `max_order_count`
- `max_trades_per_day`
- `cooldown_after_loss`
- `halt_on_stale_data`
- `halt_on_audit_mismatch`
- `halt_on_kill_switch`
- `halt_on_missing_operator_intent`

This is config visibility only. `risk_control_execution_gate_added=false`.

## Kill-Switch Display

The kill-switch section reports:

- `kill_switch_requirements_defined`
- `kill_switch_verified_for_live=false`
- `kill_switch_blocks_live_execution=true`
- `emergency_stop_documented`
- `current_kill_switch_state`

The current build treats kill-switch live verification as missing. That missing verification blocks live execution.

## Paper Summary Display

The paper summary displays paper PnL, exposure, positions count, latest paper run reference, and strategy evaluation status when those inputs exist. If paper PnL inputs are missing, the panel emits `not_available` and keeps `pnl_invented=false`.

## Static Rendering Approach

The panel supports deterministic local renderers:

- `render_operator_ui_panel_v1_json(...)`
- `render_operator_ui_panel_v1_markdown(...)`
- `render_operator_ui_panel_v1_html(...)`

HTML output is static file content only. It uses inline CSS, no external JavaScript, no CDN, no web server, and no network dependency.

The paper daily loop writes these passive artifacts when artifact writing is enabled:

- `operator_ui_panel_v1.json`
- `operator_ui_panel_v1.md`
- `operator_ui_panel_v1.html`

## Secret Boundary

The static secret-boundary policy now validates:

- operator UI panel payloads
- rendered JSON/Markdown/HTML
- action states
- risk-limit summaries
- kill-switch summaries

The policy rejects forbidden secret, signing, auth, transaction, and order payload fields such as `private_key`, `mnemonic`, `seed_phrase`, `signature`, `signed_order`, `signed_payload`, `raw_transaction`, `auth_header`, `bearer_token`, `api_key`, `access_token`, `order_submission_payload`, and `transaction_payload`.

Human acknowledgement language remains allowed only as non-cryptographic operator intent context.

## Future Work

- Implement a real risk control plane in a separate future task without enabling execution.
- Keep the live connector disabled until a separate future gated task explicitly changes that boundary.
- Define and validate any future live credential policy separately.
- Live-verify kill-switch behavior before any future live-canary proposal.
- Implement a separate dual-control live approval model before any future live canary.
- Keep the tiny canary non-executable until all future gates are explicitly cleared.
