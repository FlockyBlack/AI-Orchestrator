# ORCH-PMBOT-TRADING-MVP-061 Manual Approved Tiny Order Scaffold

## Purpose

061 adds a review-only tiny order scaffold and manual approval packet for PMBOT. It lets the operator inspect what a future supervised tiny order candidate would look like under hard caps, while preserving every current live-trading block.

The command is:

```powershell
python -m pm_bot.operator_runner.tiny_order_scaffold --market BTC --strategy tiny-momentum --dry-run
```

Optional review flags:

```text
--from-latest-signer-boundary
--from-latest-paper-intent
--max-notional
--max-size
--max-price
--artifacts-dir
--json
```

## Why 061 Does Not Enable Live Trading

The scaffold is hard-coded to `execution_mode=preflight`, `review_only=true`, `preflight_only=true`, and `scaffold_only=true`.

It does not submit orders, cancel orders, sign, generate signed payloads, instantiate a signer, read private keys, connect a wallet, fetch balances, fetch positions, fetch fills, fetch PnL, enable live trading, or add autonomous trading.

All execution-enabling flags remain false:

- `live_execution_approved=false`
- `canary_executable_now=false`
- `real_execution_available=false`
- `order_submission_enabled=false`
- `wallet_signing_enabled=false`
- `signing_enabled=false`
- `signed_payload_generation_enabled=false`
- `signed_order_generation_enabled=false`
- `authenticated_polymarket_enabled=false`
- `live_connector_enabled=false`
- `allowed_for_live=false`
- `resolved_blocker_count=0`

## Tiny Candidate vs Executable Order

Tiny order candidate is a local review object derived from the latest 060 signer boundary artifact when available, or the latest paper intent when the signer boundary artifact is missing. It contains only review fields:

- market
- strategy
- source intent path
- source signer boundary path
- candidate outcome
- candidate side
- candidate limit price
- candidate size
- candidate notional
- hard cap values
- unresolved blockers

It is not an executable order. It records `candidate_is_executable=false`, `operator_approved=false`, `signing_attempted=false`, `signed_payload_generated=false`, and `order_submission_attempted=false`.

Executable order remains unavailable because there is no signer, no signed payload, no wallet connection, no order submission path, no cancellation path, and no live approval.

## Manual Approval Packet Structure

The manual approval packet is a review-only artifact with this structure:

- source intent path
- source signer boundary path
- tiny candidate summary
- hard limits
- risk summary
- submission availability
- operator acknowledgement state
- remaining blockers

The packet always keeps:

- `approval_required=true`
- `operator_approved=false`
- `candidate_is_executable=false`
- `order_submission_available=false`
- `signed_payload_available=false`
- `allowed_for_live=false`

## Hard Caps

Default caps are deliberately tiny:

- `max_notional=1.0`
- `max_size=1.0`
- `max_price=0.99`

The scaffold marks `hard_limits_passed=true` only when a source candidate exists and the candidate limit price, size, and notional are positive and within those caps. If source data is missing or any cap fails, the scaffold writes a blocker and remains incomplete or blocked.

## Artifacts

Default artifact directory:

```text
pm_bot/trading_core/artifacts/tiny_order_scaffold_061/
```

Generated artifacts:

- `tiny_order_scaffold_061_result.json`
- `tiny_order_scaffold_061_operator.md`
- `latest_tiny_order_scaffold_status_061.json`
- `tiny_order_candidate_061.json`
- `tiny_order_hard_limits_061.json`
- `manual_tiny_order_approval_packet_061.json`
- `tiny_order_scaffold_risk_summary_061.json`
- `tiny_order_submission_availability_061.json`
- `tiny_order_scaffold_blockers_061.json`

Artifacts must remain free of raw private keys, API secrets, passphrases, auth tokens, seed phrases, mnemonics, signatures, signed payload values, fake execution identifiers, fake fills, fake balances, fake positions, and fake PnL.

## Remaining Blockers Before First Supervised Live Order

- Separate operator-approved task must explicitly relax the current no-live boundary.
- Private-key and wallet handling remain absent.
- Signer instantiation remains blocked.
- Signed payload generation remains unavailable.
- Order submission and cancellation remain unavailable.
- Balance, position, fill, and PnL reads remain unavailable.
- Live execution approval remains false.
- Any future live order task must separately validate signer, wallet, payload, approval, submission, cancellation, account-read, kill-switch, and audit boundaries.

## Operator Next Steps

Review the packet only. No live order is available from 061.

Recommended operator review:

- confirm source intent path
- confirm source signer boundary path
- inspect tiny candidate fields
- confirm hard caps
- confirm approval required
- confirm `operator_approved=false`
- confirm signing blocked
- confirm signed payload unavailable
- confirm order submission blocked
- confirm wallet blocked
- confirm live execution blocked

Do not treat any 061 artifact as trading advice, live approval, a signable payload, or an executable order.
