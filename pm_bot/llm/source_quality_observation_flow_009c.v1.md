# SOURCE-009C Source Quality Observation Flow

This local flow connects `pm_bot/llm/source_quality_observation_candidate_1987056_009b.v1.json` to future outcome tracking for market `1987056`.

It does not score sources by trade profitability. It does not create source ranking for trading decisions. It does not compute probability, EV, edge, confidence, side selection, or any market action score.

## Stages

1. Source observed.
2. Source role classified.
3. Operator reviews whether source is official or credible.
4. Outcome becomes known later.
5. Source alignment reviewed.
6. Source reliability updated.
7. Source can be preferred in future source capture, not automatically trusted for trading.

## Allowed Future Source Quality Fields

- `resolution_alignment_count`
- `contradiction_count`
- `timeliness_notes`
- `official_source_status`
- `operator_usefulness_notes`

## Forbidden Scoring Inputs

- Trade profitability
- Financial outcome
- Stake result
- Order result
- Market action result

## Safety

The flow is local-only and operator-review-only. It creates no trading authority, no execution authority, no OpenRouter calls, no Polymarket API calls, no wallet access, no orders, no runtime or dispatcher changes, no background workers, no browser automation, no queue mutation, and no canonical packet mutation.
