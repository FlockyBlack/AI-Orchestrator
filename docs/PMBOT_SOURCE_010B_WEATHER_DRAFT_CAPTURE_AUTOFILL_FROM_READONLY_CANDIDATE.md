# PMBOT SOURCE-010B Weather Draft Capture Autofill From Read-Only Candidate

SOURCE-010B is local-only. It consumes stored SOURCE-010A2 public read-only candidate artifacts and creates a manual source capture draft for market 693869.

## Outcome

- market_id: 693869
- market_class: weather
- draft_capture_created: true
- capture_status: draft
- operator_review_required: true
- ready_for_local_review is not auto-set
- real_ingested_template_count_after: 3
- draft_ingested_template_count_after: 3
- ready_ingested_template_count_after: 0
- future_live_002_allowed: false

## Pipeline

- SOURCE-010A2 read-only artifacts are copied into a SOURCE-004-compatible manual capture draft.
- SOURCE-005 ingest can include the draft only with `--include-drafts`.
- SOURCE-006 readiness remains blocked from future live approval while captures are draft-only.
- Operator review is still required.

## Safety Boundary

- no network or API calls in SOURCE-010B
- no OpenRouter calls
- no orders
- no recommendations
- no side choice
- no probability, EV, edge, or confidence score
- no source scoring
- no wallet access
- no queue, runtime, dispatcher, background, browser, or canonical packet mutation
