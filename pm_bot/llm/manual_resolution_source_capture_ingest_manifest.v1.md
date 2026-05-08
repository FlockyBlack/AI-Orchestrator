# PMBOT SOURCE-005 Manual Capture Ingest Manifest

- schema_version: manual_resolution_source_capture_ingest_manifest.v1
- task_id: PMBOT-SOURCE-005-MANUAL-CAPTURE-INGEST-FROM-FILLED-TEMPLATES
- status: manual_capture_ingest_manifest_created
- capture_dir: pm_bot/llm/manual_resolution_source_capture
- example_dir: pm_bot/llm/manual_resolution_source_capture_examples
- total_real_template_count: 16
- real_filled_template_count: 3
- real_ingested_template_count: 3
- sandbox_example_count: 1
- skipped_empty_count: 13
- skipped_placeholder_count: 0
- skipped_example_count: 1
- canonical_packets_mutated: false

## Capture Status Counts

- not_started: 13
- draft: 3
- ready_for_local_review: 0
- reviewed: 0
- needs_revision: 0

## Required Ingest Fields

- full_market_resolution_criteria_text
- full_resolution_rules
- official_source_references
- official_source_urls_or_rule_references
- source_timestamps
- source_reliability_review
- reviewed_local_evidence_references
- non_placeholder_evidence_notes

## Eligible Market IDs

- 1987056
- 597964
- 693869

## Sandbox Example Paths

- pm_bot/llm/manual_resolution_source_capture_examples/example_filled_capture.v1.json
