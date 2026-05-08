# PMBOT SOURCE-005 Manual Capture Ingest From Filled Templates

SOURCE-005 adds a local ingest layer for manually filled SOURCE-004 templates.
It does not treat empty real templates or sandbox examples as source improvement.

## Result

- ingest_status: real_templates_ingested
- reason: none
- real_filled_template_count: 2
- real_ingested_template_count: 2
- sandbox_example_count: 1
- skipped_empty_count: 13
- skipped_placeholder_count: 0
- skipped_example_count: 1

## Ingest Rules

- Skip `not_started` templates.
- Skip empty or placeholder required source fields.
- Skip sandbox/example templates.
- Default ingest accepts `ready_for_local_review` and `reviewed` records.
- `--include-drafts` allows fully filled `draft` records.
- `--strict-ready` keeps the ingest limited to review-ready statuses.

## Current Honest State

- At least one real capture template was ingested into the overlay.

## Safety Boundary

- no OpenRouter calls
- no Polymarket API calls
- no network calls
- no trading authority
- no queue, runtime, dispatcher, background, browser, wallet, or order authority
- no market action guidance
- no probability, EV, edge, confidence, or side selection

## Next Action

- Fill one real capture template from manual local source review, then rerun `python -m pm_bot.llm.ingest_manual_resolution_source_capture --write --summary-only`.
