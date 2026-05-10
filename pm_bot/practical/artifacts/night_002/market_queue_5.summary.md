# PMBOT Market Queue Summary

- Generated at: `2026-05-10T00:00:00Z`
- Queue items: 6

## Status counts

- `analysis_ready`: 1
- `blocked`: 1
- `feedback_complete`: 1
- `hypothesis_active`: 1
- `outcome_pending`: 1
- `queued`: 1

## Markets

- `queue-weather-001` `queued` - Will the synthetic city record measurable rain on June 1?
  Next: Run local packet import if needed, then run finite local analysis.
  Blockers: none
- `queue-crypto-001` `analysis_ready` - Will the synthetic token close above the reference level on June 2?
  Next: Inspect the analysis card and decide whether to track the paper-only hypothesis.
  Blockers: none
- `queue-politics-001` `hypothesis_active` - Will the synthetic policy measure pass committee by June 3?
  Next: Wait for a local outcome record or add one when the outcome is known.
  Blockers: none
- `queue-esports-001` `outcome_pending` - Will synthetic Team Azure win the map-three match on June 4?
  Next: Add a resolved local outcome record when available.
  Blockers: none
- `queue-generic-001` `feedback_complete` - Will the synthetic event certificate be filed by June 5?
  Next: Review feedback lessons and update the source learning ledger.
  Blockers: none
- `queue-blocked-001` `blocked` - Will the synthetic city record measurable rain on June 1?
  Next: Resolve the local blockers before continuing this queue item.
  Blockers: Local packet missing required evidence file.; Missing linked artifact `local_input_path` at `pm_bot/tests/fixtures/practical_market_queue_batch/inputs/missing.blocked.json`

## Missing linked artifacts

- `queue-blocked-001` missing `local_input_path` at `pm_bot/tests/fixtures/practical_market_queue_batch/inputs/missing.blocked.json`

## Safety boundary

- Local queue JSON and linked local artifacts only.
- No live fetch, API key, wallet, order, or trading action is used.
- Operator actions are workflow steps, not market instructions.
