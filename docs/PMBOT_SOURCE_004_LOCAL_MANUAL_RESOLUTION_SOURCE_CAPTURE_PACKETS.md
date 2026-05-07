# PMBOT SOURCE-004 Local Manual Resolution Source Capture Packets

## Executive Summary

SOURCE-004 created a local-only manual capture layer for the 14 current PMBOT inventory markets. It adds a schema, one JSON and one Markdown capture template per market, a manifest, and a validator report. All templates are `not_started` and contain no fetched or invented source data.

## Why SOURCE-004 Was Needed After SOURCE-003

SOURCE-003 proved that the normalizer worked but the local packets did not contain rich resolution/source/rules data to normalize. SOURCE-004 therefore creates operator-fillable packets so a human can capture those missing fields consistently before any later local scoring or analysis review.

## Capture Templates Created

- capture_market_count: 14
- capture_json_template_count: 14
- capture_markdown_template_count: 14
- capture_directory: pm_bot/llm/manual_resolution_source_capture/
- manifest: pm_bot/llm/manual_resolution_source_capture_manifest.v1.json
- validation_report: pm_bot/llm/manual_resolution_source_capture_validation.v1.json

## How An Operator Should Use Them

1. Paste or summarize official resolution criteria if available locally.
2. Add source/rule references if manually verified.
3. Add source timestamp.
4. Add reliability note.
5. Do not add predictions or trading guidance.

## Fields Remaining Empty

- full_market_resolution_criteria_text: 14
- full_resolution_rules: 14
- official_source_references: 14
- official_source_urls_or_rule_references: 14
- source_timestamps: 14
- source_reliability_review: 14
- reviewed_local_evidence_references: 14
- non_placeholder_evidence_notes: 14

## Validation Summary

- total_packets_validated: 14
- valid_count: 14
- invalid_count: 0
- packets_not_started: 14
- packets_ready_for_local_review: 0

## Workbench Dashboard Updates

- operator_openrouter_review_dashboard includes a manual resolution/source capture summary.
- operator_review_pack includes manifest and validation pointers.
- operator_workbench_export_run includes capture status, validation status, and no-authority flags.

## Limitations

- No source data was fetched, invented, or filled from memory.
- Templates are not_started and require human operator input before local review readiness.
- Validation checks template shape and safety boundaries; it does not verify external facts.

## Next Recommended Tasks

- Option A: PMBOT-SOURCE-005-SOURCE-GAP-NORMALIZATION - normalize source gap notes and reliability fields across manually captured packets after operator input.
- Option B: PMBOT-SOURCE-006-UNREVIEWED-PACKET-CHECKLIST-RISK-CONTEXT-BUILDER - improve checklist/risk/contradiction sections for the 4 unreviewed packets.
- Option C: PMBOT-SOURCE-007-MANUAL-CAPTURE-INGEST-FROM-FILLED-TEMPLATES - once operator fills templates, ingest them into local packet readiness scoring.
- Option D: PMBOT-OPENROUTER-054-REPEAT-N5-READINESS-PROTOCOL-AFTER-SOURCE-GATE - protocol-only repeat N=5 readiness after manual capture review, no live calls.

These future tasks are documented only; they were not run or approved by SOURCE-004.

## Explicit Safety Statement

- no OpenRouter calls
- no Polymarket API calls
- no network calls
- no trading
- no wallet/orders
- no runtime/dispatcher/background/browser/queue changes
- no API key access
- no market recommendations
- no probability/EV/edge/confidence/side selection
