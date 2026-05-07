# PMBOT Source Evidence Gap Plan By Category v1

- schema_version: source_evidence_gap_plan_by_category.v1
- task_id: PMBOT-SOURCE-001-EVIDENCE-ENRICHMENT-DESIGN-FROM-INVENTORY
- status: gap_plan_created
- category_count: 5
- no_market_action_guidance: true

## Category Plans

### company/business

- market_ids_in_category: 691547, 692258
- recommended_priority: high
- estimated_effort: medium
- common_medium-completeness_causes: full local resolution/source/rule text is absent or weak; official source references and timestamps are absent from local packets; local evidence remains placeholder or source-gap oriented; unreviewed packets lack local contradiction, risk, and operator checklist sections
- required_local_enrichment_fields_to_reach_high: full_market_resolution_criteria_text, official_source_or_rule_reference_notes, explicit_source_gap_notes, contradiction_check_context, risk_notes_context, operator_checklist, category_specific_key_fields, entity, event_definition, instrument_or_business_action_if_applicable, date_or_resolution_window, source_timestamps_when_present_locally
- future_task_suggestion: Normalize company/business source/rule fields from local packets and produce operator-review-only completeness updates.

### crypto

- market_ids_in_category: 573656
- recommended_priority: high
- estimated_effort: small
- common_medium-completeness_causes: full local resolution/source/rule text is absent or weak; official source references and timestamps are absent from local packets; local evidence remains placeholder or source-gap oriented; reviewed OpenRouter artifacts are medium completeness rather than high
- required_local_enrichment_fields_to_reach_high: full_market_resolution_criteria_text, official_source_or_rule_reference_notes, explicit_source_gap_notes, contradiction_check_context, risk_notes_context, operator_checklist, category_specific_key_fields, asset_or_ticker, threshold, date_or_resolution_window, settlement_condition, benchmark_and_timezone_rules, source_timestamps_when_present_locally
- future_task_suggestion: Normalize crypto source/rule fields from local packets and produce operator-review-only completeness updates.

### elections

- market_ids_in_category: 569332, 569333, 569334, 569343, 569344, 569366, 569368, 569373, 598936
- recommended_priority: high
- estimated_effort: large
- common_medium-completeness_causes: full local resolution/source/rule text is absent or weak; official source references and timestamps are absent from local packets; local evidence remains placeholder or source-gap oriented; reviewed OpenRouter artifacts are medium completeness rather than high; unreviewed packets lack local contradiction, risk, and operator checklist sections
- required_local_enrichment_fields_to_reach_high: full_market_resolution_criteria_text, official_source_or_rule_reference_notes, explicit_source_gap_notes, contradiction_check_context, risk_notes_context, operator_checklist, category_specific_key_fields, jurisdiction, office_or_election_event, candidate_or_party_if_applicable, date_or_resolution_window, official_election_authority_identifier_if_available, source_timestamps_when_present_locally
- future_task_suggestion: Normalize elections source/rule fields from local packets and produce operator-review-only completeness updates.

### legal/courts

- market_ids_in_category: 563650
- recommended_priority: high
- estimated_effort: small
- common_medium-completeness_causes: full local resolution/source/rule text is absent or weak; official source references and timestamps are absent from local packets; local evidence remains placeholder or source-gap oriented; reviewed OpenRouter artifacts are medium completeness rather than high
- required_local_enrichment_fields_to_reach_high: full_market_resolution_criteria_text, official_source_or_rule_reference_notes, explicit_source_gap_notes, contradiction_check_context, risk_notes_context, operator_checklist, category_specific_key_fields, court_or_legal_body, case_or_event_definition, docket_identifier_if_available, decision_or_acceptance_condition, date_or_resolution_window, source_timestamps_when_present_locally
- future_task_suggestion: Normalize legal/courts source/rule fields from local packets and produce operator-review-only completeness updates.

### politics

- market_ids_in_category: 597964
- recommended_priority: high
- estimated_effort: small
- common_medium-completeness_causes: full local resolution/source/rule text is absent or weak; official source references and timestamps are absent from local packets; local evidence remains placeholder or source-gap oriented; unreviewed packets lack local contradiction, risk, and operator checklist sections
- required_local_enrichment_fields_to_reach_high: full_market_resolution_criteria_text, official_source_or_rule_reference_notes, explicit_source_gap_notes, contradiction_check_context, risk_notes_context, operator_checklist, category_specific_key_fields, jurisdiction, office_or_public_role, named_person_or_institution, event_definition, date_or_resolution_window, source_timestamps_when_present_locally
- future_task_suggestion: Normalize politics source/rule fields from local packets and produce operator-review-only completeness updates.

## Safety

- planning only
- no live adapters
- no network calls
