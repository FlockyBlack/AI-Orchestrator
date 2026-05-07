# PMBOT Local Source Enrichment Action Plan v1

- schema_version: local_source_enrichment_action_plan.v1
- task_id: PMBOT-SOURCE-003-RESOLUTION-SOURCE-FIELD-NORMALIZATION
- status: local_source_enrichment_action_plan_created
- plan_type: passive_local_proposal_not_runtime_queue

## Aggregate

- total_actions: 14
- high_priority_local_actions: 4
- medium_priority_local_actions: 10
- low_priority_local_actions: 0

## Fields To Fix First

- full_market_resolution_criteria_text
- full_resolution_rules
- official_source_references
- official_source_urls_or_rule_references
- source_timestamps
- source_reliability_review

## Proposed Future Task Order

1. local manual resolution source capture
2. source gap normalization
3. packet completeness scorer rerun
4. repeat N=5 readiness protocol only after readiness review

## Per-Market Passive Actions

- 563650: priority=medium; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review; requires_external_network=false; operator_manual_input_needed=true
- 569332: priority=medium; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review; requires_external_network=false; operator_manual_input_needed=true
- 569333: priority=medium; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review; requires_external_network=false; operator_manual_input_needed=true
- 569334: priority=medium; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review; requires_external_network=false; operator_manual_input_needed=true
- 569343: priority=medium; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review; requires_external_network=false; operator_manual_input_needed=true
- 569344: priority=medium; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review; requires_external_network=false; operator_manual_input_needed=true
- 569366: priority=medium; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review; requires_external_network=false; operator_manual_input_needed=true
- 569368: priority=medium; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review; requires_external_network=false; operator_manual_input_needed=true
- 569373: priority=medium; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review; requires_external_network=false; operator_manual_input_needed=true
- 573656: priority=medium; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review; requires_external_network=false; operator_manual_input_needed=true
- 597964: priority=high; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review; requires_external_network=false; operator_manual_input_needed=true
- 598936: priority=high; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review; requires_external_network=false; operator_manual_input_needed=true
- 691547: priority=high; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review; requires_external_network=false; operator_manual_input_needed=true
- 692258: priority=high; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review; requires_external_network=false; operator_manual_input_needed=true

## Safety

- queue_mutation_performed: false
- runtime_objects_created: false
- dispatcher_integration_added: false
- no_market_action_guidance: true
- openrouter_calls_performed: 0
- polymarket_api_calls_performed: 0
- external_network_calls_performed: 0
