# PMBOT SOURCE-004C Sandbox Manual Capture Fill Workflow

SOURCE-004C adds one visibly sandbox-only filled capture example. It proves the operator workflow shape without modifying real market capture templates or inventing real source data.

## Artifacts

- pm_bot/llm/manual_resolution_source_capture_examples/example_filled_capture.v1.json
- pm_bot/llm/manual_resolution_source_capture_examples/example_filled_capture.v1.md
- pm_bot/llm/manual_resolution_source_capture_examples/example_filled_capture_manifest.v1.json
- pm_bot/llm/manual_resolution_source_capture_examples/example_filled_capture_manifest.v1.md

## Boundary Flags

- example_only: true
- sandbox_only: true
- not_real_market_data: true
- not_for_ingest_as_real_source: true
- analysis_only: true
- operator_review_only: true
- no_market_action_guidance: true

## Real Template Policy

- The 14 real capture templates under `pm_bot/llm/manual_resolution_source_capture/` are unchanged.
- The sandbox example is not counted as real filled market data.
- SOURCE-005 ingest must skip this example.
- SOURCE-006 readiness must count this example separately from real source progress.

## Safety Boundary

- no OpenRouter calls
- no Polymarket API calls
- no network calls
- no trading authority
- no queue, runtime, dispatcher, background, browser, wallet, or order authority
- no market action guidance
- no probability, EV, edge, confidence, or side selection
