# Manual Resolution Source Capture - 1987056

- contract_version: manual_resolution_source_capture.v1
- schema_version: manual_resolution_source_capture_schema.v1
- task_id: PMBOT-SOURCE-009B-ESPORTS-DRAFT-CAPTURE-AUTOFILL-FROM-READONLY-CANDIDATE
- market_id: 1987056
- market_class: esports
- market_title_or_question: LoL: JD Gaming vs Anyone's Legend (BO5) - Esports World Cup China Qualifier Phase 2
- current_openrouter_review_status: not_reviewed
- current_readiness_band: draft_from_readonly_candidate
- source_capture_status: draft
- capture_status: draft
- operator_review_required: true
- auto_promote_to_ready_for_local_review: false

## Source Capture

### Full Market Resolution Criteria Text

This market refers to the LoL Upper bracket final match between JD Gaming and Anyone's Legend in the Esports World Cup China Qualifier Phase 2, initially scheduled for May 21 at 4:00AM ET.

This market will resolve to "JD Gaming" if JD Gaming win the match against Anyone's Legend.

This market will resolve to "Anyone's Legend" if Anyone's Legend win the match against JD Gaming.

If the match is canceled (not played at all), ends in a tie, or is delayed beyond 7 days from the scheduled date without a winner determined, this market will resolve to 50-50.

If the match begins but is not completed, and one team wins due to the opponent's forfeiture, disqualification, or walkover, this market will resolve to the team who wins.

If the match ends in a forfeit, disqualification, or walkover (team withdraws before the start and the other wins automatically), this market will resolve to 50-50.

The resolution source for this market will be official information from https://gol.gg/esports/home. However, if https://gol.gg/esports/home has not published final results within 2 hours after the event\u2019s conclusion, a consensus of credible reporting may be used instead including video evidence.

In cases where a team\u2019s listed name includes minor discrepancies from the resolution source, this market will resolve based on the underlying real-world match rather than exact name matching. Recognizable abbreviations, alternate or erroneous spellings, sponsor tags, affiliate or academy designations, regional identifiers, and minor formatting differences will be treated as referring to the same team, provided the intended team can be clearly and uniquely identified within the relevant competition. If a listed team name has no reasonable connection to any participating team, or if it matches or could reasonably refer to another team in the same competition such that the intended team cannot be unambiguously determined, this market will resolve 50-50.

### Full Resolution Rules

This market refers to the LoL Upper bracket final match between JD Gaming and Anyone's Legend in the Esports World Cup China Qualifier Phase 2, initially scheduled for May 21 at 4:00AM ET.

This market will resolve to "JD Gaming" if JD Gaming win the match against Anyone's Legend.

This market will resolve to "Anyone's Legend" if Anyone's Legend win the match against JD Gaming.

If the match is canceled (not played at all), ends in a tie, or is delayed beyond 7 days from the scheduled date without a winner determined, this market will resolve to 50-50.

If the match begins but is not completed, and one team wins due to the opponent's forfeiture, disqualification, or walkover, this market will resolve to the team who wins.

If the match ends in a forfeit, disqualification, or walkover (team withdraws before the start and the other wins automatically), this market will resolve to 50-50.

The resolution source for this market will be official information from https://gol.gg/esports/home. However, if https://gol.gg/esports/home has not published final results within 2 hours after the event\u2019s conclusion, a consensus of credible reporting may be used instead including video evidence.

In cases where a team\u2019s listed name includes minor discrepancies from the resolution source, this market will resolve based on the underlying real-world match rather than exact name matching. Recognizable abbreviations, alternate or erroneous spellings, sponsor tags, affiliate or academy designations, regional identifiers, and minor formatting differences will be treated as referring to the same team, provided the intended team can be clearly and uniquely identified within the relevant competition. If a listed team name has no reasonable connection to any participating team, or if it matches or could reasonably refer to another team in the same competition such that the intended team cannot be unambiguously determined, this market will resolve 50-50.

### Official Source References

- SOURCE-009A read-only Gamma market metadata artifact for market-specific rules text
- https://gol.gg/esports/home

### Source URLs Or Rule References

- https://gol.gg/esports/home
- pm_bot/live_readonly/esports_market_discovery/esports_source_capture_candidate_009a.v1.json

### Source Timestamps

- SOURCE-009A read-only fetch marker: 2026-05-08T00:00:00Z_SOURCE_009A_READONLY_FIELD_TEST
- Scheduled match time from normalized candidate: 2026-05-21T09:00:00Z
- SOURCE-009B local autofill timestamp: 2026-05-08 Asia/Tbilisi; no network calls performed.

### Source Reliability Review

SOURCE-009A provides locally stored public read-only Gamma metadata for rules text. The market metadata names https://gol.gg/esports/home as the official result source, but SOURCE-009B does not fetch or verify any live result page. Operator review must verify the exact rules text, source hierarchy, event identity, and timing before any status promotion.

### Reviewed Local Evidence References

- pm_bot/live_readonly/esports_market_discovery/esports_market_raw_fetch_009a.v1.json
- pm_bot/live_readonly/esports_market_discovery/esports_market_normalized_candidate_009a.v1.json
- pm_bot/live_readonly/esports_market_discovery/esports_source_capture_candidate_009a.v1.json
- pm_bot/live_readonly/esports_market_discovery/esports_operator_review_checklist_009a.v1.json
- pm_bot/live_readonly/esports_market_discovery/esports_operator_review_checklist_009a.v1.md

### Evidence Notes

SOURCE-009A locally stored Gamma metadata contains the esports market description, rules text, named result source, event/tournament context, teams, game title, and scheduled time. SOURCE-009B copies that evidence into a manual capture draft only; operator review remains required and no market decision is made.

## Unresolved Source Questions

- Operator must verify exact Polymarket/Gamma rules text before any status promotion.
- Operator must verify match, tournament, game, team names, timezone, and event schedule.
- Operator must verify cancellation, reschedule, forfeit, walkover, delay, and name discrepancy handling.
- Operator must verify the official result source and fallback source hierarchy around event conclusion.
- Operator must verify cancellation, reschedule, forfeit, and walkover handling.

## Operator Instructions

- Verify exact Polymarket/Gamma rules text against the stored 009A candidate and any approved local source review surface.
- Verify official result source and fallback source hierarchy.
- Verify event identity, teams, scheduled time, and timezone.
- Verify cancellation, reschedule, forfeit, walkover, delay, and name discrepancy handling.
- Keep this capture as draft until operator review is complete.
- Do not add predictions, market action guidance, probability, EV, edge, confidence, or side selection.

## Safety Summary

- local-only draft from SOURCE-009A artifacts
- no OpenRouter calls
- no Polymarket API calls in SOURCE-009B
- no external network calls
- no market action guidance
- no probability, EV, edge, confidence scoring, or side selection
- no trading, queue, runtime, dispatcher, background, browser, wallet, or order authority
