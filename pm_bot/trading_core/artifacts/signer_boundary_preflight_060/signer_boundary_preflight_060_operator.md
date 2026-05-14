# PMBOT Signer Boundary Preflight 060

- Status: `signer_boundary_preflight_completed_live_blocked`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Mode: `preflight / review-only`
- execution_mode: `preflight`
- review_only: `true`
- preflight_only: `true`

## Source Intent

- Source intent path: `pm_bot/trading_core/artifacts/paper_trading_loop_053/paper_trading_order_intent_053.json`
- Live candidate intent status: `created`
- Candidate outcome: `Yes`
- Candidate side: `paper_track_outcome`
- Candidate limit price: `0.52`
- Candidate size: `1.0`
- Candidate notional: `0.52`
- Candidate intent is non-executable: `true`

## Unsigned Plan

- Unsigned plan status: `schema_only_non_executable`
- unsigned_plan_created: `true`
- unsigned_plan_is_executable=false
- Schema-only plan: `true`
- Real CLOB payload materialized: `false`
- Ready for signing: `false`

## Boundary Status

- Signer blocked: `true`
- Signed payload unavailable: `true`
- Order submission blocked: `true`
- Wallet blocked: `true`
- Live execution blocked: `true`
- private_key_read: `false`
- seed_phrase_read: `false`
- mnemonic_read: `false`
- wallet_connection_attempted: `false`
- signer_instantiated: `false`
- signing_attempted: `false`
- signed_payload_generated: `false`
- order_submission_attempted: `false`
- order_cancellation_attempted: `false`
- balance_read_attempted: `false`
- position_read_attempted: `false`
- live_execution_approved: `false`
- allowed_for_live: `false`
- resolved_blocker_count: `0`

## Blockers

- Signer is unavailable and blocked; no signer is configured or instantiated.
- Signed payload generation is unavailable and blocked.
- Order submission and cancellation are blocked.
- Wallet connection and wallet signing remain blocked.
- Live execution approval is false; no live action is available.

## Next Operator Action

- review signer boundary only, no live order available
- Latest status path: `pm_bot/trading_core/artifacts/signer_boundary_preflight_060/latest_signer_boundary_preflight_status_060.json`
