# ORCH-PMBOT-TRADING-MVP-063 Supervised Tiny Live Enablement Gate

## Purpose

063 adds a supervised tiny live enablement preparation gate for a future first-live-order task. It records operator approval boundaries, tiny intended limits, kill/cancel/failure plans, environment readiness markers, and unresolved execution blockers.

This is preparation only. It does not enable live trading, sign, instantiate a signer, connect a wallet, submit orders, cancel orders, call authenticated trading endpoints, read private keys or API secrets, or fetch balances, positions, fills, PnL, order IDs, transaction hashes, or execution results.

## Command

```powershell
python -m pm_bot.operator_runner.supervised_tiny_live_enablement_gate --market BTC --strategy tiny-momentum --dry-run
```

`--dry-run` is required. Live, wallet, signing, submission, cancellation, authenticated trading, account runtime, and fake execution identifier flags are rejected by the runner.

## Scope

The gate references existing 061/062 preparation artifacts when present:

- 061 tiny order scaffold
- 062P pre-live tiny order gate

Those references are informational. Missing or present source artifacts do not make the 063 packet executable.

## Required False Flags

All 063 outputs preserve:

- `live_execution_approved=false`
- `canary_executable_now=false`
- `real_execution_available=false`
- `order_submission_enabled=false`
- `order_cancel_enabled=false`
- `wallet_signing_enabled=false`
- `signing_enabled=false`
- `signed_payload_generation_enabled=false`
- `signed_order_generation_enabled=false`
- `authenticated_polymarket_enabled=false`
- `live_connector_enabled=false`
- `allowed_for_live=false`
- `operator_approved=false`
- `candidate_is_executable=false`
- `resolved_blocker_count=0`

## Tiny Intended Limits

The risk limits are non-executable preparation constraints:

- `max_order_notional_usd <= 1.00`
- `max_daily_notional_usd <= 1.00`
- `max_orders_per_day = 1`
- `max_market_count = 1`
- `allowed_market = BTC`
- `allowed_strategy = tiny-momentum`

A later explicit live-enabling task and operator approval are still required.

## Plans

063 writes descriptive, non-executable plans:

- Kill switch plan: how the operator stops future live enablement by withholding approval and preserving blockers.
- Cancel plan: what must exist in a later approved task before any real order could be considered.
- Failure plan: what to do in a later task if placement, API, auth, network, wallet, signer, or cancellation readiness fails.

These plans do not perform actions and do not add runtime capabilities.

## Environment Readiness

Environment readiness is presence-only and redacted. It checks only non-secret readiness marker labels, records booleans, and emits no raw values. Missing markers keep live enablement blocked.

## Manual Approval Packet

The manual packet states:

- `operator_approved=false`
- `approval_required=true`
- `approval_scope=first_tiny_live_order_preparation_only`
- the packet is not executable
- a later explicit live-enabling task is required
- no order can be submitted from this packet

## Required Unresolved Blockers

The blocker matrix always includes these unresolved blockers:

- `operator_approved_false`
- `live_enablement_task_not_present`
- `private_key_unavailable_and_not_read`
- `wallet_unavailable`
- `signer_unavailable`
- `signing_unavailable`
- `signed_payload_generation_unavailable`
- `order_submission_unavailable`
- `order_cancel_unavailable`
- `authenticated_trading_unavailable`
- `balances_positions_fills_pnl_unavailable`
- `live_execution_not_approved`
- `candidate_non_executable`

`resolved_blocker_count` remains `0`.

## Artifacts

063 writes:

- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_enablement_gate_063_result.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_enablement_gate_063_operator.md`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/latest_supervised_tiny_live_enablement_status_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_operator_checklist_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_blockers_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_risk_limits_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_kill_switch_plan_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_cancel_plan_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_failure_plan_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_env_readiness_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_manual_approval_packet_063.json`
