# PMBOT SOURCE-009B Esports Draft Capture Autofill From Read-Only Candidate

SOURCE-009B is local-only. It consumes stored SOURCE-009A public read-only candidate artifacts and creates a manual source capture draft for market 1987056.

## Outcome

- market_id: 1987056
- market_class: esports
- draft_capture_created: true
- capture_status: draft
- operator_review_required: true
- real_ingested_template_count_after: 2
- draft_ingested_template_count_after: 2
- ready_ingested_template_count_after: 0
- future_live_002_allowed: false

## Pipeline

- SOURCE-009A read-only artifacts are copied into a SOURCE-004-compatible manual capture draft.
- SOURCE-005 ingest can include the draft only with `--include-drafts`.
- SOURCE-006 readiness remains blocked from future live approval while captures are draft-only.
- ready_for_local_review is not auto-set.

## Safety Boundary

- no orders
- no recommendations
- no side choice
- no probability, EV, edge, or confidence score
- no OpenRouter calls
- no Polymarket API calls in SOURCE-009B
- no external network calls
- no queue, runtime, dispatcher, background, browser, wallet, or order authority
