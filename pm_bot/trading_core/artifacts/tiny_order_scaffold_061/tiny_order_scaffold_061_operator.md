# PMBOT Tiny Order Scaffold 061

- Status: `tiny_order_scaffold_completed_live_blocked`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Mode: `preflight / review-only`
- execution_mode: `preflight`
- review_only: `true`
- preflight_only: `true`
- scaffold_only: `true`

## Source

- Source intent path: `pm_bot/trading_core/artifacts/paper_trading_loop_053/paper_trading_order_intent_053.json`
- Source signer boundary path: `pm_bot/trading_core/artifacts/signer_boundary_preflight_060/latest_signer_boundary_preflight_status_060.json`

## Tiny Candidate

- Tiny candidate status: `created`
- Candidate outcome: `Yes`
- Candidate side: `paper_track_outcome`
- Candidate limit price: `0.52`
- Candidate size: `1.0`
- Candidate notional: `0.52`
- candidate executable=false

## Hard Limits

- max_notional: `1.0`
- max_size: `1.0`
- max_price: `0.99`
- hard_limits_passed: `true`

## Manual Approval Packet

- approval required: `true`
- operator approved=false
- approval packet created: `true`
- candidate executable=false

## Submission Availability

- signing blocked
- signed payload unavailable: `true`
- order submission blocked
- order cancellation blocked
- wallet blocked
- balance reads blocked
- position reads blocked
- fill reads blocked
- live execution blocked
- signed_payload_available: `false`
- order_submission_available: `false`
- live_execution_approved: `false`
- allowed_for_live: `false`
- resolved_blocker_count: `0`

## Blockers

- Manual operator approval is required and operator_approved remains false.
- Signing remains blocked; no signer is configured or instantiated.
- Signed payload generation is unavailable and blocked.
- Order submission and cancellation are blocked.
- Wallet connection and wallet signing remain blocked.
- Balance, position, fill, and PnL reads remain blocked.
- Live execution approval is false; no live action is available.

## Next Operator Action

- review packet only; no live order available
- Latest status path: `pm_bot/trading_core/artifacts/tiny_order_scaffold_061/latest_tiny_order_scaffold_status_061.json`
