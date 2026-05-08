# PMBOT SOURCE-004C Sandbox Filled Capture Example

- task_id: PMBOT-SOURCE-004C-SANDBOX-MANUAL-CAPTURE-FILL-WORKFLOW
- market_id: example_source_004c_sandbox
- example_only: true
- sandbox_only: true
- not_real_market_data: true
- not_for_ingest_as_real_source: true
- analysis_only: true
- operator_review_only: true
- no_market_action_guidance: true

## Purpose

This file demonstrates the shape of a filled manual source capture record without adding real market data. It must never be counted as real source evidence or ingested as a real market source.

## Filled Fields

- full_market_resolution_criteria_text: fictional example criteria for a non-real event.
- full_resolution_rules: fictional example rules for a mock rule document.
- official_source_references: Example Official Rule Document (sandbox).
- official_source_urls_or_rule_references: example-rule-reference://sandbox/local-rule-section-1.
- source_timestamps: 2026-05-08T00:00:00+04:00 for the sandbox source label.
- source_reliability_review: sandbox-only format demonstration.
- reviewed_local_evidence_references: pm_bot/llm/manual_resolution_source_capture_examples/example_filled_capture.v1.json.
- non_placeholder_evidence_notes: shape demonstration only; not real source evidence.

## Safety Boundary

- no OpenRouter calls
- no Polymarket API calls
- no network calls
- no trading authority
- no queue, runtime, dispatcher, background, browser, wallet, or order authority
- no market action guidance
- no probability, EV, edge, confidence, or side selection
