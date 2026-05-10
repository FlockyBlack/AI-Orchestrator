# PMBOT Practical Operator Console

## Queue summary

- `analysis_ready`: 1
- `blocked`: 1
- `feedback_complete`: 1
- `hypothesis_active`: 1
- `outcome_pending`: 1
- `queued`: 1

## Active paper hypotheses

- Active paper hypotheses: 4
- Unresolved outcomes: 3

## Outcome checks

- Feedback pending: 0

## Feedback pending

- `synthetic-generic-event-001` - Review feedback lessons and update the source learning ledger.

## Source learning summary

- `contradictory`: 2
- `insufficient`: 2
- `misleading`: 2
- `stale`: 1
- `unknown`: 2
- `useful`: 3

## Blockers

- `queue-blocked-001`: Local packet missing required evidence file.; Missing linked artifact `local_input_path` at `pm_bot/tests/fixtures/practical_market_queue_batch/inputs/missing.blocked.json`

## Next practical actions

- `synthetic-weather-rain-001` - Run local packet import if needed, then run finite local analysis.
- `synthetic-crypto-reference-001` - Inspect the analysis card and decide whether to track the paper-only hypothesis.
- `synthetic-politics-measure-001` - Wait for a local outcome record or add one when the outcome is known.
- `synthetic-esports-match-001` - Add a resolved local outcome record when available.
- `synthetic-generic-event-001` - Review feedback lessons and update the source learning ledger.
- `synthetic-weather-rain-001` - Resolve the local blockers before continuing this queue item.

## Safety boundary

- Local artifacts only.
- Paper-only analysis-quality tracking.
- No live fetch, real trade decision, wallet access, order, or trading action is used.
