# PMBOT Manual Resolution Source Capture Validation v1

- schema_version: manual_resolution_source_capture_validation.v1
- capture_schema_version: manual_resolution_source_capture_schema.v1
- task_id: PMBOT-SOURCE-004-LOCAL-MANUAL-RESOLUTION-SOURCE-CAPTURE-PACKETS
- status: manual_resolution_source_capture_validation_passed
- strict_ready_enabled: false
- total_packets_validated: 14
- valid_count: 14
- invalid_count: 0
- packets_ready_for_local_review: 0
- packets_not_started: 14

## Missing Required Template Fields

- none

## Missing Fields By Priority

- priority=1 field=full_market_resolution_criteria_text market_count=14
- priority=2 field=full_resolution_rules market_count=14
- priority=3 field=official_source_references market_count=14
- priority=4 field=official_source_urls_or_rule_references market_count=14
- priority=5 field=source_timestamps market_count=14
- priority=6 field=source_reliability_review market_count=14
- priority=7 field=reviewed_local_evidence_references market_count=14
- priority=8 field=non_placeholder_evidence_notes market_count=14

## Operator Next Steps

- Open a not_started capture template and fill priority fields from manual local review.
- Set both source_capture_status and capture_status to draft after substantive local input starts.
- Run python -m pm_bot.llm.manual_resolution_source_capture_validator --write after edits.

## Market Action Guidance Findings

- none

## Packets Not Started

- 563650, 569332, 569333, 569334, 569343, 569344, 569366, 569368, 569373, 573656, 597964, 598936, 691547, 692258

## Safety Summary

- openrouter_calls_performed: 0
- polymarket_api_calls_performed: 0
- external_network_calls_performed: 0
- no_market_action_guidance: true
- no_trading_authority: true
- no_queue_authority: true
- no_runtime_authority: true
- no_wallet_or_order_authority: true
- validation_command: python -m pm_bot.llm.manual_resolution_source_capture_validator --write
