# PMBOT Current LLM Resolution Source Normalization Audit v1

- schema_version: current_llm_resolution_source_normalization_audit.v1
- task_id: PMBOT-SOURCE-003-RESOLUTION-SOURCE-FIELD-NORMALIZATION
- status: resolution_source_normalization_audit_created
- generated_by: pm_bot/llm/resolution_source_normalizer.py
- source_inventory_path: pm_bot/llm/current_llm_market_packet_inventory.v1.json

## Aggregate

- total_markets_audited: 14
- markets_with_resolution_criteria_text: 0
- markets_missing_resolution_criteria_text: 14
- markets_with_full_resolution_rules: 0
- markets_missing_full_resolution_rules: 14
- markets_with_official_source_references: 0
- markets_missing_official_source_references: 14
- markets_with_official_source_urls_or_rule_references: 0
- markets_missing_official_source_urls_or_rule_references: 14
- markets_with_source_timestamps: 0
- markets_missing_source_timestamps: 14
- markets_with_source_reliability_review: 0
- markets_missing_source_reliability_review: 14
- markets_needing_manual_resolution_source_review: 14

## Top Resolution Source Gaps

- full_market_resolution_criteria_text: 14
- full_resolution_rules: 14
- official_source_references: 14
- official_source_urls_or_rule_references: 14
- source_timestamps: 14
- source_reliability_review: 14

## Per-Market Audit

- 563650: category=legal/courts; criteria_present=false; rules_present=false; official_refs_present=false; manual_review_needed=true; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review
- 569332: category=elections; criteria_present=false; rules_present=false; official_refs_present=false; manual_review_needed=true; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review
- 569333: category=elections; criteria_present=false; rules_present=false; official_refs_present=false; manual_review_needed=true; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review
- 569334: category=elections; criteria_present=false; rules_present=false; official_refs_present=false; manual_review_needed=true; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review
- 569343: category=elections; criteria_present=false; rules_present=false; official_refs_present=false; manual_review_needed=true; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review
- 569344: category=elections; criteria_present=false; rules_present=false; official_refs_present=false; manual_review_needed=true; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review
- 569366: category=elections; criteria_present=false; rules_present=false; official_refs_present=false; manual_review_needed=true; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review
- 569368: category=elections; criteria_present=false; rules_present=false; official_refs_present=false; manual_review_needed=true; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review
- 569373: category=elections; criteria_present=false; rules_present=false; official_refs_present=false; manual_review_needed=true; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review
- 573656: category=crypto; criteria_present=false; rules_present=false; official_refs_present=false; manual_review_needed=true; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review
- 597964: category=politics; criteria_present=false; rules_present=false; official_refs_present=false; manual_review_needed=true; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review
- 598936: category=elections; criteria_present=false; rules_present=false; official_refs_present=false; manual_review_needed=true; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review
- 691547: category=company/business; criteria_present=false; rules_present=false; official_refs_present=false; manual_review_needed=true; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review
- 692258: category=company/business; criteria_present=false; rules_present=false; official_refs_present=false; manual_review_needed=true; missing=full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review

## Recommended Next Local Actions

- local manual resolution source capture
- normalize source gap notes after manual capture
- rerun packet completeness scorer after local capture
- repeat readiness protocol only after source gate review

## Safety

- local_only: true
- operator_review_only: true
- no_live_calls: true
- no_trading_authority: true
- no_queue_authority: true
- no_runtime_authority: true
- no_dispatcher_authority: true
- no_wallet_or_order_authority: true
- acceptance_is_not_trading_approval: true
- no_market_action_guidance: true
- openrouter_calls_performed: 0
- polymarket_api_calls_performed: 0
- external_network_calls_performed: 0
