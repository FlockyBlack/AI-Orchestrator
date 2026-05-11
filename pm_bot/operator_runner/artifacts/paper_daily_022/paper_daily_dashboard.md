# PMBOT Paper Daily Dashboard

- Run ID: `paper-daily-loop-022-2026-05-11`
- Run date: `2026-05-11`
- Tracked markets: 6
- Unresolved markets: 6
- Feedback ready: 0
- Paper intents: 6
- Risk allowed: 6
- Risk blocked: 0
- Simulated executions: 6
- Simulated fills: 2
- Open paper positions: 2
- Carried-forward positions: 2
- Total paper exposure: `$50.0`

## Tracked Markets

- `563650` `unresolved` - SCOTUS accepts sports event contract case by July 31, 2026?
- `597964` `unresolved` - Macron out by June 30, 2026?
- `598936` `unresolved` - Will the next UK election be called by June 30, 2026?
- `691547` `unresolved` - Kraken IPO by December 31, 2026?
- `692258` `unresolved` - MicroStrategy sells any Bitcoin by June 30, 2026?
- `573656` `unresolved` - Will Bitcoin hit $150k by December 31, 2026?

## Open Paper Positions

- `563650` `$25.0` `unresolved`
- `691547` `$25.0` `unresolved`

## Carried-Forward Positions

- `563650` `$25.0` `unresolved`
- `691547` `$25.0` `unresolved`

## Feedback Readiness

- total_tracked_markets: `6`
- unresolved_count: `6`
- resolved_count: `0`
- feedback_ready_count: `0`
- blocked_feedback_count: `6`

## Blocked, Rejected, Skipped

- Blocked: 0
- Rejected: 0
- Skipped: 4

## Idempotency

- idempotency_mode: `upsert_by_run_date_market_intent`
- new_applied_count: `0`
- already_applied_count: `2`
- already_open_position_count: `0`
- duplicate_fill_prevented_count: `2`
- carried_forward_position_count: `2`
- idempotency_passed: `True`

## Safety Flags

- real_order_submitted: `false`
- wallet_used: `false`
- private_key_used: `false`
- signing_used: `false`
- trading_endpoint_used: `false`
- real_money_used: `false`
- autonomous_trading_enabled: `false`
- authenticated_endpoint_used: `false`
- browser_automation_used: `false`
- openrouter_used: `false`
- polymarket_api_used: `false`
- outcome_invented: `false`

## Next Operator Action

- Review carried-forward open paper positions and exposure before the next local paper run.
- Recheck unresolved markets only against saved local outcome artifacts.
- Prepare feedback records only for markets with explicit local resolution evidence.
- Keep this as an explicit one-shot local command, not a scheduler or autonomous loop.
