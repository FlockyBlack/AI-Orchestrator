# PMBOT Supervised Tiny Live Enablement Gate 063

- Status: `supervised_tiny_live_enablement_prepared_live_blocked`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Mode: `supervised tiny live enablement preparation / review-only`
- execution_mode: `preflight`
- preparation_only: `true`
- non_executable: `true`

## Source Artifacts

- Pre-live tiny order gate 062P: `pm_bot/trading_core/artifacts/pre_live_tiny_order_gate_062p/latest_pre_live_tiny_order_gate_status_062p.json`
- Tiny order scaffold 061: `pm_bot/trading_core/artifacts/tiny_order_scaffold_061/latest_tiny_order_scaffold_status_061.json`

## Tiny Limits

- max_order_notional_usd: `1.0`
- max_daily_notional_usd: `1.0`
- max_orders_per_day: `1`
- max_market_count: `1`
- allowed_market: `BTC`
- allowed_strategy: `tiny-momentum`
- preparation constraints only; not executable

## Manual Approval Packet

- approval_required: `true`
- approval_scope: `first_tiny_live_order_preparation_only`
- operator_approved=false
- this packet is not executable
- a later explicit live-enabling task is required
- no order can be submitted from this packet

## Environment Readiness

- marker_count: `8`
- missing_marker_count: `8`
- presence_only=true
- values_redacted=true
- raw_values_emitted=false

## Descriptive Plans

- kill switch plan exists and is not executable
- cancellation prerequisites exist and are not executable
- failure plan exists and is not executable

## Blockers

- `operator_approved_false` - operator_approved remains false; this preparation gate cannot approve live execution.
- `live_enablement_task_not_present` - A separate explicit live-enabling task is required before any first tiny live order.
- `private_key_unavailable_and_not_read` - Private key material is unavailable and was not read.
- `wallet_unavailable` - Wallet connection and wallet signing are unavailable.
- `signer_unavailable` - Signer runtime is unavailable and not instantiated.
- `signing_unavailable` - Signing is unavailable and blocked.
- `signed_payload_generation_unavailable` - Signed payload generation is unavailable and blocked.
- `order_submission_unavailable` - Order submission is unavailable and blocked.
- `order_cancel_unavailable` - Order cancellation is unavailable and blocked.
- `authenticated_trading_unavailable` - Authenticated trading calls are unavailable and blocked.
- `balances_positions_fills_pnl_unavailable` - Balance, position, fill, and PnL runtime reads are unavailable and blocked.
- `live_execution_not_approved` - Live execution approval is false and allowed_for_live remains false.
- `candidate_non_executable` - candidate_is_executable remains false; any candidate is preparation-only.

## Required False Flags

- live_execution_approved=false
- canary_executable_now=false
- real_execution_available=false
- order_submission_enabled=false
- order_cancel_enabled=false
- wallet_signing_enabled=false
- signing_enabled=false
- signed_payload_generation_enabled=false
- signed_order_generation_enabled=false
- authenticated_polymarket_enabled=false
- live_connector_enabled=false
- allowed_for_live=false
- operator_approved=false
- candidate_is_executable=false
- resolved_blocker_count=0
