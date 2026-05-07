# PMBOT Manual Resolution Source Capture Schema v1

- schema_version: manual_resolution_source_capture_schema.v1
- contract_version: manual_resolution_source_capture.v1
- task_id: PMBOT-SOURCE-004-LOCAL-MANUAL-RESOLUTION-SOURCE-CAPTURE-PACKETS
- status: manual_resolution_source_capture_schema_created
- schema_scope: local_manual_source_evidence_capture_only

## Safety Rules

- Do not include trading recommendations.
- Do not include market predictions.
- Do not include probability, EV, edge, confidence, or side selection.
- Do not include buy/sell/hold/enter/exit language.
- Capture is for source/evidence completeness only.

## Capture Status Values

- not_started
- draft
- ready_for_local_review
- reviewed
- needs_revision

## Fields

- market_id: type=string, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- market_title_or_question: type=string_or_null, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- category: type=string_or_null, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- capture_status: type=enum, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- full_market_resolution_criteria_text: type=string, required_template_field=true, required_for_high_completeness=true, recommended_before_openrouter_review=false
- full_resolution_rules: type=string, required_template_field=true, required_for_high_completeness=true, recommended_before_openrouter_review=false
- official_source_references: type=array, required_template_field=true, required_for_high_completeness=true, recommended_before_openrouter_review=false
- official_source_urls_or_rule_references: type=array, required_template_field=true, required_for_high_completeness=true, recommended_before_openrouter_review=false
- source_timestamps: type=array, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- source_reliability_review: type=string, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=true
- reviewed_local_evidence_references: type=array, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=true
- non_placeholder_evidence_notes: type=string, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- jurisdiction: type=string_or_null, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- candidate_or_party_if_applicable: type=string_or_null, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- manual_operator_notes: type=string, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- unresolved_source_questions: type=array, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- source_capture_author_or_operator: type=string_or_null, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- source_capture_timestamp_local: type=string_or_null, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- source_capture_provenance: type=string, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- no_market_action_guidance: type=boolean, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- operator_review_only: type=boolean, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- no_trading_authority: type=boolean, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- no_queue_authority: type=boolean, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- no_runtime_authority: type=boolean, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false
- no_wallet_or_order_authority: type=boolean, required_template_field=true, required_for_high_completeness=false, recommended_before_openrouter_review=false

## Required For High Completeness

- full_market_resolution_criteria_text
- full_resolution_rules
- official_source_references
- official_source_urls_or_rule_references

## Recommended Before OpenRouter Review

- source_reliability_review
- reviewed_local_evidence_references

## No Authority Flags

- no_market_action_guidance: true
- no_queue_authority: true
- no_runtime_authority: true
- no_trading_authority: true
- no_wallet_or_order_authority: true
- operator_review_only: true
