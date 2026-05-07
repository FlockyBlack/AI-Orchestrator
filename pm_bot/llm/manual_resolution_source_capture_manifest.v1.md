# PMBOT Manual Resolution Source Capture Manifest v1

- schema_version: manual_resolution_source_capture_manifest.v1
- contract_version: manual_resolution_source_capture.v1
- task_id: PMBOT-SOURCE-004-LOCAL-MANUAL-RESOLUTION-SOURCE-CAPTURE-PACKETS
- status: manual_resolution_source_capture_manifest_created
- total_capture_packets: 14
- no_market_action_guidance: true

## Capture Status Counts

- not_started: 14
- draft: 0
- ready_for_local_review: 0
- reviewed: 0
- needs_revision: 0

## Readiness Band Counts

- low: 4
- medium: 10

## Reviewed vs Unreviewed

- reviewed_accepted: 10
- reviewed_blocked: 0
- not_reviewed: 4
- unknown: 0
- reviewed_market_ids: 563650, 569332, 569333, 569334, 569343, 569344, 569366, 569368, 569373, 573656
- unreviewed_market_ids: 597964, 598936, 691547, 692258

## Markets By Category

- company/business: 691547, 692258
- crypto: 573656
- elections: 569332, 569333, 569334, 569343, 569344, 569366, 569368, 569373, 598936
- legal/courts: 563650
- politics: 597964

## Fields Missing Across All Packets

- full_market_resolution_criteria_text: 14
- full_resolution_rules: 14
- official_source_references: 14
- official_source_urls_or_rule_references: 14
- source_timestamps: 14
- source_reliability_review: 14
- reviewed_local_evidence_references: 14
- non_placeholder_evidence_notes: 14

## Required For High Completeness

- full_market_resolution_criteria_text
- full_resolution_rules
- official_source_references
- official_source_urls_or_rule_references

## Recommended Operator Fill Order

1. full_market_resolution_criteria_text
2. full_resolution_rules
3. official_source_references
4. official_source_urls_or_rule_references
5. source_timestamps
6. source_reliability_review
7. reviewed_local_evidence_references
8. non_placeholder_evidence_notes

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

## Packet Paths

- pm_bot/llm/manual_resolution_source_capture/563650_resolution_source_capture.v1.json
- pm_bot/llm/manual_resolution_source_capture/569332_resolution_source_capture.v1.json
- pm_bot/llm/manual_resolution_source_capture/569333_resolution_source_capture.v1.json
- pm_bot/llm/manual_resolution_source_capture/569334_resolution_source_capture.v1.json
- pm_bot/llm/manual_resolution_source_capture/569343_resolution_source_capture.v1.json
- pm_bot/llm/manual_resolution_source_capture/569344_resolution_source_capture.v1.json
- pm_bot/llm/manual_resolution_source_capture/569366_resolution_source_capture.v1.json
- pm_bot/llm/manual_resolution_source_capture/569368_resolution_source_capture.v1.json
- pm_bot/llm/manual_resolution_source_capture/569373_resolution_source_capture.v1.json
- pm_bot/llm/manual_resolution_source_capture/573656_resolution_source_capture.v1.json
- pm_bot/llm/manual_resolution_source_capture/597964_resolution_source_capture.v1.json
- pm_bot/llm/manual_resolution_source_capture/598936_resolution_source_capture.v1.json
- pm_bot/llm/manual_resolution_source_capture/691547_resolution_source_capture.v1.json
- pm_bot/llm/manual_resolution_source_capture/692258_resolution_source_capture.v1.json

## Markdown Paths

- pm_bot/llm/manual_resolution_source_capture/563650_resolution_source_capture.v1.md
- pm_bot/llm/manual_resolution_source_capture/569332_resolution_source_capture.v1.md
- pm_bot/llm/manual_resolution_source_capture/569333_resolution_source_capture.v1.md
- pm_bot/llm/manual_resolution_source_capture/569334_resolution_source_capture.v1.md
- pm_bot/llm/manual_resolution_source_capture/569343_resolution_source_capture.v1.md
- pm_bot/llm/manual_resolution_source_capture/569344_resolution_source_capture.v1.md
- pm_bot/llm/manual_resolution_source_capture/569366_resolution_source_capture.v1.md
- pm_bot/llm/manual_resolution_source_capture/569368_resolution_source_capture.v1.md
- pm_bot/llm/manual_resolution_source_capture/569373_resolution_source_capture.v1.md
- pm_bot/llm/manual_resolution_source_capture/573656_resolution_source_capture.v1.md
- pm_bot/llm/manual_resolution_source_capture/597964_resolution_source_capture.v1.md
- pm_bot/llm/manual_resolution_source_capture/598936_resolution_source_capture.v1.md
- pm_bot/llm/manual_resolution_source_capture/691547_resolution_source_capture.v1.md
- pm_bot/llm/manual_resolution_source_capture/692258_resolution_source_capture.v1.md
