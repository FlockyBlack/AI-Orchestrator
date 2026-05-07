# PMBOT Manual Resolution Source Capture Progress v1

- schema_version: manual_resolution_source_capture_progress.v1
- task_id: PMBOT-SOURCE-004B-MANUAL-CAPTURE-OPERATOR-FILL-GUIDE
- total_templates: 14
- not_started_count: 14
- draft_count: 0
- ready_for_local_review_count: 0
- reviewed_count: 0
- needs_revision_count: 0
- valid_template_count: 14
- invalid_template_count: 0
- validation_command: python -m pm_bot.llm.manual_resolution_source_capture_validator --write

## Fields Filled Counts

- full_market_resolution_criteria_text: 0
- full_resolution_rules: 0
- official_source_references: 0
- official_source_urls_or_rule_references: 0
- source_timestamps: 0
- source_reliability_review: 0
- reviewed_local_evidence_references: 0
- non_placeholder_evidence_notes: 0

## Fields Missing Counts

- full_market_resolution_criteria_text: 14
- full_resolution_rules: 14
- official_source_references: 14
- official_source_urls_or_rule_references: 14
- source_timestamps: 14
- source_reliability_review: 14
- reviewed_local_evidence_references: 14
- non_placeholder_evidence_notes: 14

## Next Fields To Fill

- full_market_resolution_criteria_text
- full_resolution_rules
- official_source_references
- official_source_urls_or_rule_references
- source_timestamps
- source_reliability_review
- reviewed_local_evidence_references
- non_placeholder_evidence_notes

## Markets Ready For Local Review

- none

## Markets Needing Operator Input

- 563650
- 569332
- 569333
- 569334
- 569343
- 569344
- 569366
- 569368
- 569373
- 573656
- 597964
- 598936
- 691547
- 692258

## Recommended Operator Next Action

- Open one not_started capture JSON and its Markdown companion, fill the recommended fields from manual local review, set both status fields to draft, then rerun validation.

## Safety Summary

- no OpenRouter calls
- no Polymarket API calls
- no network calls
- no trading
- no wallet/orders
- no runtime/dispatcher/background/browser/queue changes
- no API key access
- no market recommendations
- no probability, EV, edge, confidence, or side selection
