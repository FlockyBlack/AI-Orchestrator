# PMBOT Paper Canary Drill 052

- Status: `paper_canary_drill_completed`
- Market: `BTC fixture`
- Mode: `paper / review-only`
- Live execution: `blocked`
- Fixture mode: `true`
- Network used: `false`
- Review-only status feed: `pm_bot/trading_core/artifacts/paper_canary_drill_052/latest_paper_canary_status_052.json`

## Market Snapshot

- Market ID: `pm-agents-052-btc-fixture-market`
- Slug: `btc-paper-canary-fixture-052`
- Source: `local_polymarket_agents_reference_fixture_052`

## Paper Intent

- Status: `paper_order_intent_review_ready`
- Market: `pm-agents-052-btc-fixture-market` / `btc-paper-canary-fixture-052`
- Notional USD: `1.0`
- Limit price: `0.53`
- This is not order submission.

## Risk And Gates

- Risk decision: `BLOCK`
- Go/no-go: `NO_GO`
- Go/no-go status: `NO_GO_UNRESOLVED_BLOCKERS`
- Resolved blockers: `0`

## Required False Flags

- live_execution_approved: `false`
- canary_executable_now: `false`
- real_execution_available: `false`
- order_submission_enabled: `false`
- wallet_signing_enabled: `false`
- signing_enabled: `false`
- signed_payload_generation_enabled: `false`
- signed_order_generation_enabled: `false`
- authenticated_polymarket_enabled: `false`
- live_connector_enabled: `false`
- allowed_for_live: `false`

## Artifacts

- normalized_market: `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_normalized_market_052.json`
- market_snapshot: `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_market_snapshot_052.json`
- order_intent: `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_order_intent_052.json`
- risk_readiness: `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_risk_readiness_052.json`
- gonogo: `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_gonogo_052.json`
- approval_packet: `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_supervised_approval_packet_052.json`
- approval_packet_md: `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_supervised_approval_packet_052.md`
- result: `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_result.json`
- operator_md: `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_operator.md`
- latest_status: `pm_bot/trading_core/artifacts/paper_canary_drill_052/latest_paper_canary_status_052.json`
- latest_status_md: `pm_bot/trading_core/artifacts/paper_canary_drill_052/latest_paper_canary_status_052.md`

## Safety

- No wallet connection, signing, authenticated Polymarket call, or real order submission is available.
- No order, transaction, fill, balance, or profit/loss execution result is generated.
