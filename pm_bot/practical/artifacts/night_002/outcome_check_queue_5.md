# PMBOT Outcome Check Queue

- Generated at: `2026-05-10T00:00:00Z`

## Status counts

- `due_now`: 1
- `not_due`: 2
- `overdue`: 1
- `resolved`: 1
- `unknown`: 1

## Outcome checks

- `synthetic-weather-rain-001` `not_due` - Will the synthetic city record measurable rain on June 1?
  Next: No local outcome check is needed yet.
- `synthetic-crypto-reference-001` `not_due` - Will the synthetic token close above the reference level on June 2?
  Next: No local outcome check is needed yet.
- `synthetic-politics-measure-001` `due_now` - Will the synthetic policy measure pass committee by June 3?
  Next: Look for a local outcome record and attach it to the queue item.
- `synthetic-esports-match-001` `overdue` - Will synthetic Team Azure win the map-three match on June 4?
  Next: Attach or update the local outcome record before feedback review.
- `synthetic-generic-event-001` `resolved` - Will the synthetic event certificate be filed by June 5?
  Next: Run local paper feedback if it has not been generated.
- `synthetic-weather-rain-001` `unknown` - Will the synthetic city record measurable rain on June 1?
  Next: Resolve queue blockers or inspect the local outcome record path.

## Safety boundary

- Local outcome records only.
- No live outcome lookup is performed.
