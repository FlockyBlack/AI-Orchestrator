# PMBOT Source Learning Ledger

- Ledger ID: `source_learning_ledger.86375b12d34e`
- Generated at: `2026-05-10T00:00:00Z`
- Feedback records: 6
- Markets: 5

## Source usefulness summary

- `contradictory`: 2
- `insufficient`: 2
- `misleading`: 2
- `stale`: 1
- `unknown`: 2
- `useful`: 3

## Source records

- `crypto_archived_reference` (Synthetic Archived Reference Close): `stale` across 1 market(s).
- `crypto_rules_capture` (Synthetic Crypto Rules Capture): `useful` across 1 market(s).
- `esports_match_note` (Synthetic Match Note): `misleading` across 1 market(s).
- `esports_roster_note` (Synthetic Roster Note): `misleading` across 1 market(s).
- `generic_event_rules` (Synthetic Event Rules Note): `insufficient` across 1 market(s).
- `generic_planning_note` (Synthetic Planning Note): `insufficient` across 1 market(s).
- `politics_committee_note_a` (Synthetic Committee Note A): `contradictory` across 1 market(s).
- `politics_committee_note_b` (Synthetic Committee Note B): `contradictory` across 1 market(s).
- `weather_event_note` (Synthetic Event Note): `useful` across 1 market(s).
- `weather_station_bulletin` (Synthetic Station Bulletin): `useful` across 1 market(s).

## Source failure patterns

- 2 source observation(s) labeled contradictory.
- 2 source observation(s) labeled insufficient.
- 2 source observation(s) labeled misleading.
- 1 source observation(s) labeled stale.
- 2 source observation(s) labeled unknown.

## Recommended source handling updates

- Require freshness review for stale local source packets.
- Separate source claim capture from reasoning review for misleading observations.
- Keep contradiction notes visible before feedback review.
- Pair insufficient sources with explicit missing-evidence capture.

## Analysis prompt improvement notes

- Add a required material-missing-evidence check before analysis completion.
- Add a required reasoning audit note for each key claim.
- Keep the current compact card shape and source attribution fields.
- Keep the outcome placeholder visible until a resolved local record exists.

## Safety

- No autonomous training was performed.
- No real trade decision was produced.
- Source learning is a transparent ledger update from local feedback artifacts only.

## Batch source observations

- `crypto_archived_reference` `stale` from `synthetic-crypto-reference-001.analysis.7384b905ed0b.feedback.43c63ed7fd61`
- `crypto_rules_capture` `useful` from `synthetic-crypto-reference-001.analysis.7384b905ed0b.feedback.43c63ed7fd61`
- `esports_match_note` `misleading` from `synthetic-esports-match-001.analysis.a6d4bc90b97b.feedback.1eec6af56a38`
- `esports_roster_note` `misleading` from `synthetic-esports-match-001.analysis.a6d4bc90b97b.feedback.1eec6af56a38`
- `generic_event_rules` `insufficient` from `synthetic-generic-event-001.analysis.11f645d06c7a.feedback.fb0d436d5783`
- `generic_planning_note` `insufficient` from `synthetic-generic-event-001.analysis.11f645d06c7a.feedback.fb0d436d5783`
- `politics_committee_note_a` `contradictory` from `synthetic-politics-measure-001.analysis.b32ac6067fb8.feedback.128c574bbbfb`
- `politics_committee_note_b` `contradictory` from `synthetic-politics-measure-001.analysis.b32ac6067fb8.feedback.128c574bbbfb`
- `weather_event_note` `unknown` from `synthetic-weather-rain-001.analysis.6ba2343c0bce.feedback.30bc2b9cebcf`
- `weather_event_note` `useful` from `synthetic-weather-rain-001.analysis.6ba2343c0bce.feedback.5728109c45aa`
- `weather_station_bulletin` `unknown` from `synthetic-weather-rain-001.analysis.6ba2343c0bce.feedback.30bc2b9cebcf`
- `weather_station_bulletin` `useful` from `synthetic-weather-rain-001.analysis.6ba2343c0bce.feedback.5728109c45aa`

## Batch safety note

- Source learning is a transparent ledger aggregation only.
- No autonomous training was performed.
