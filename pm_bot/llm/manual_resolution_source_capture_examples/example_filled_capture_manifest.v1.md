# PMBOT SOURCE-004C Sandbox Filled Capture Manifest

- schema_version: manual_resolution_source_capture_example_manifest.v1
- task_id: PMBOT-SOURCE-004C-SANDBOX-MANUAL-CAPTURE-FILL-WORKFLOW
- status: sandbox_example_manifest_created
- example_only: true
- sandbox_only: true
- not_real_market_data: true
- not_for_ingest_as_real_source: true
- sandbox_example_count: 1
- real_market_template_count: 0
- real_market_templates_modified: false
- real_source_data_invented: false

## Example Paths

- pm_bot/llm/manual_resolution_source_capture_examples/example_filled_capture.v1.json
- pm_bot/llm/manual_resolution_source_capture_examples/example_filled_capture.v1.md

## Safety Boundary

- no OpenRouter calls
- no Polymarket API calls
- no network calls
- no trading authority
- no queue, runtime, dispatcher, background, browser, wallet, or order authority
- no market action guidance
- no probability, EV, edge, confidence, or side selection
